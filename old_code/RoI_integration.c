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

#define WIDTH 256
#define HEIGHT 256
#define FPS 30
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

int main() {
    avformat_network_init();
    avcodec_register_all();

    const AVCodec *codec = avcodec_find_encoder_by_name("libx264");
    if (!codec) {
        fprintf(stderr, "Codec not found\n");
        return -1;
    }

    AVCodecContext *ctx = avcodec_alloc_context3(codec);
    ctx->width = WIDTH;
    ctx->height = HEIGHT;
    ctx->time_base = (AVRational){1, FPS};
    ctx->framerate = (AVRational){FPS, 1};
    ctx->pix_fmt = AV_PIX_FMT_YUV420P;
    ctx->gop_size = 10;
    ctx->max_b_frames = 1;
    ctx->bit_rate = 400000;

    av_opt_set(ctx->priv_data, "aq-mode", "1", 0);
    av_opt_set(ctx->priv_data, "crf", "23", 0);

    if (avcodec_open2(ctx, codec, NULL) < 0) {
        fprintf(stderr, "Could not open codec\n");
        return -1;
    }

    AVFrame *frame = av_frame_alloc();
    frame->format = ctx->pix_fmt;
    frame->width  = ctx->width;
    frame->height = ctx->height;
    av_frame_get_buffer(frame, 32);

    AVPacket *pkt = av_packet_alloc();

    for (int i = 0; i < 30; i++) {
        av_frame_make_writable(frame);
        for (int y = 0; y < ctx->height; y++) {
            for (int x = 0; x < ctx->width; x++) {
                frame->data[0][y * frame->linesize[0] + x] = x + y + i * 3;
            }
        }
        for (int y = 0; y < ctx->height / 2; y++) {
            for (int x = 0; x < ctx->width / 2; x++) {
                frame->data[1][y * frame->linesize[1] + x] = 128;
                frame->data[2][y * frame->linesize[2] + x] = 64;
            }
        }

        frame->pts = i;
        inject_rois_into_frame(frame);

        if (avcodec_send_frame(ctx, frame) < 0) {
            fprintf(stderr, "Error sending frame\n");
            break;
        }

        while (avcodec_receive_packet(ctx, pkt) == 0) {
            printf("Encoded frame %d, size=%d\n", i, pkt->size);
            av_packet_unref(pkt);
        }
    }

    avcodec_send_frame(ctx, NULL); // flush
    while (avcodec_receive_packet(ctx, pkt) == 0) {
        printf("Flushed packet, size=%d\n", pkt->size);
        av_packet_unref(pkt);
    }

    av_packet_free(&pkt);
    av_frame_free(&frame);
    avcodec_free_context(&ctx);
    return 0;
}
