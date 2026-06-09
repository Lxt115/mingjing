#pragma once
#include "cJSON.h"
#include <stdint.h>
#include <stdbool.h>

#define PROTO_BUF_SIZE 8192

typedef enum {
    PROTO_MSG_WELCOME,
    PROTO_MSG_TRANSCRIPT,
    PROTO_MSG_TEXT_CHUNK,
    PROTO_MSG_AUDIO_CHUNK,
    PROTO_MSG_AUDIO_DONE,
    PROTO_MSG_ERROR,
    PROTO_MSG_UNKNOWN,
} proto_msg_type_t;

typedef struct {
    proto_msg_type_t type;
    char text[1024];
    char content[PROTO_BUF_SIZE];
    int  content_len;
    bool has_audio;
} proto_msg_t;

int  proto_build_audio_start(char *buf, int max_len);
int  proto_build_audio_chunk(char *buf, int max_len, const uint8_t *audio_b64, int b64_len);
int  proto_build_audio_end(char *buf, int max_len);
bool proto_parse(const char *json_str, int len, proto_msg_t *out);
