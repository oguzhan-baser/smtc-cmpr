#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libavutil/opt.h>
#include <libavutil/imgutils.h>
#include <libavutil/rational.h>
#include <libavutil/frame.h>
#include <libavutil/mem.h>
#include <libavutil/pixdesc.h>
#include <libswscale/swscale.h>
#include <stdio.h>

#define ROI_COUNT 5

int inject_rois_into_frame(AVFrame *frame) {
    AVRegionOfInterest *rois = av_mallocz(sizeof(*rois) * ROI_COUNT);
    if (!rois)
        return AVERROR(ENOMEM);

    rois[0] = (AVRegionOfInterest){ .self_size = sizeof(AVRegionOfInterest), .top = 0,  .bottom = 16,  .left = 48,  .right = 64,  .qoffset = {0, 1}, .priority = 0 };
    rois[1] = (AVRegionOfInterest){ .self_size = sizeof(AVRegionOfInterest), .top = 0,  .bottom = 16,  .left = 128, .right = 144, .qoffset = {0, 1}, .priority = 0 };
    rois[2] = (AVRegionOfInterest){ .self_size = sizeof(AVRegionOfInterest), .top = 0,  .bottom = 32,  .left = 176, .right = 192, .qoffset = {0, 1}, .priority = 0 };
    rois[3] = (AVRegionOfInterest){ .self_size = sizeof(AVRegionOfInterest), .top = 16, .bottom = 32,  .left = 0,   .right = 16,  .qoffset = {1, 1}, .priority = 0 };
    rois[4] = (AVRegionOfInterest){ .self_size = sizeof(AVRegionOfInterest), .top = 16, .bottom = 48,  .left = 32,  .right = 48,  .qoffset = {1, 1}, .priority = 0 };

    AVFrameSideData *sd = av_frame_new_side_data(frame, AV_FRAME_DATA_REGIONS_OF_INTEREST,
                                                 sizeof(*rois) * ROI_COUNT);
    if (!sd) {
        av_free(rois);
        return AVERROR(ENOMEM);
    }
    memcpy(sd->data, rois, sizeof(*rois) * ROI_COUNT);
    av_free(rois);
    return 0;
}

int main(int argc, char *argv[]) {
    if (argc < 3) {
        fprintf(stderr, "Usage: %s input.mp4 output.mp4\n", argv[0]);
        return 1;
    }

    const char *input_filename = argv[1];
    const char *output_filename = argv[2];

    AVFormatContext *input_fmt_ctx = NULL;
    avformat_open_input(&input_fmt_ctx, input_filename, NULL, NULL);
    avformat_find_stream_info(input_fmt_ctx, NULL);

    int video_stream_index = -1;
    for (unsigned i = 0; i < input_fmt_ctx->nb_streams; i++) {
        if (input_fmt_ctx->streams[i]->codecpar->codec_type == AVMEDIA_TYPE_VIDEO) {
            video_stream_index = i;
            break;
        }
    }

    AVCodec *decoder = avcodec_find_decoder(input_fmt_ctx->streams[video_stream_index]->codecpar->codec_id);
    AVCodecContext *dec_ctx = avcodec_alloc_context3(decoder);
    avcodec_parameters_to_context(dec_ctx, input_fmt_ctx->streams[video_stream_index]->codecpar);
    avcodec_open2(dec_ctx, decoder, NULL);

    AVFormatContext *output_fmt_ctx = NULL;
    avformat_alloc_output_context2(&output_fmt_ctx, NULL, NULL, output_filename);

    AVCodec *encoder = avcodec_find_encoder_by_name("libx264");
    AVStream *out_stream = avformat_new_stream(output_fmt_ctx, encoder);
    AVCodecContext *enc_ctx = avcodec_alloc_context3(encoder);

    enc_ctx->height = dec_ctx->height;
    enc_ctx->width = dec_ctx->width;
    enc_ctx->sample_aspect_ratio = dec_ctx->sample_aspect_ratio;
    enc_ctx->pix_fmt = AV_PIX_FMT_YUV420P;
    enc_ctx->time_base = (AVRational){1, 30};
    enc_ctx->framerate = (AVRational){30, 1};
    enc_ctx->bit_rate = 400000;
    enc_ctx->gop_size = 10;

    av_opt_set(enc_ctx->priv_data, "aq-mode", "1", 0);
    av_opt_set(enc_ctx->priv_data, "crf", "23", 0);

    avcodec_open2(enc_ctx, encoder, NULL);
    avcodec_parameters_from_context(out_stream->codecpar, enc_ctx);

    if (!(output_fmt_ctx->oformat->flags & AVFMT_NOFILE))
        avio_open(&output_fmt_ctx->pb, output_filename, AVIO_FLAG_WRITE);

    avformat_write_header(output_fmt_ctx, NULL);

    struct SwsContext *sws_ctx = sws_getContext(
        dec_ctx->width, dec_ctx->height, dec_ctx->pix_fmt,
        enc_ctx->width, enc_ctx->height, enc_ctx->pix_fmt,
        SWS_BILINEAR, NULL, NULL, NULL);

    AVFrame *in_frame = av_frame_alloc();
    AVFrame *out_frame = av_frame_alloc();
    out_frame->format = enc_ctx->pix_fmt;
    out_frame->width = enc_ctx->width;
    out_frame->height = enc_ctx->height;
    av_frame_get_buffer(out_frame, 32);

    AVPacket *pkt = av_packet_alloc();
    int frame_index = 0;

    while (av_read_frame(input_fmt_ctx, pkt) >= 0) {
        if (pkt->stream_index == video_stream_index) {
            avcodec_send_packet(dec_ctx, pkt);
            while (avcodec_receive_frame(dec_ctx, in_frame) == 0) {
                sws_scale(sws_ctx,
                          (const uint8_t * const*)in_frame->data, in_frame->linesize,
                          0, dec_ctx->height,
                          out_frame->data, out_frame->linesize);
                out_frame->pts = frame_index++;
                inject_rois_into_frame(out_frame);

                avcodec_send_frame(enc_ctx, out_frame);
                AVPacket enc_pkt;
                av_init_packet(&enc_pkt);
                enc_pkt.data = NULL;
                enc_pkt.size = 0;

                while (avcodec_receive_packet(enc_ctx, &enc_pkt) == 0) {
                    enc_pkt.stream_index = out_stream->index;
                    av_interleaved_write_frame(output_fmt_ctx, &enc_pkt);
                    av_packet_unref(&enc_pkt);
                }
            }
        }
        av_packet_unref(pkt);
    }

    avcodec_send_frame(enc_ctx, NULL);
    AVPacket flush_pkt;
    av_init_packet(&flush_pkt);
    flush_pkt.data = NULL;
    flush_pkt.size = 0;
    while (avcodec_receive_packet(enc_ctx, &flush_pkt) == 0) {
        flush_pkt.stream_index = out_stream->index;
        av_interleaved_write_frame(output_fmt_ctx, &flush_pkt);
        av_packet_unref(&flush_pkt);
    }

    av_write_trailer(output_fmt_ctx);
    avcodec_free_context(&enc_ctx);
    avcodec_free_context(&dec_ctx);
    avformat_close_input(&input_fmt_ctx);
    if (!(output_fmt_ctx->oformat->flags & AVFMT_NOFILE))
        avio_closep(&output_fmt_ctx->pb);
    avformat_free_context(output_fmt_ctx);
    av_frame_free(&in_frame);
    av_frame_free(&out_frame);
    av_packet_free(&pkt);
    return 0;
}
