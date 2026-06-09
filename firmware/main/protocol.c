#include "protocol.h"
#include "cJSON.h"
#include <stdio.h>
#include <string.h>

int proto_build_audio_start(char *buf, int max_len) {
    return snprintf(buf, max_len, "{\"type\":\"audio_start\"}");
}

int proto_build_audio_chunk(char *buf, int max_len, const uint8_t *audio_b64, int b64_len) {
    int off = snprintf(buf, max_len, "{\"type\":\"audio_chunk\",\"data\":\"");
    if (off + b64_len + 3 > max_len) return off;
    memcpy(buf + off, audio_b64, b64_len);
    off += b64_len;
    off += snprintf(buf + off, max_len - off, "\"}");
    return off;
}

int proto_build_audio_end(char *buf, int max_len) {
    return snprintf(buf, max_len, "{\"type\":\"audio_end\"}");
}

bool proto_parse(const char *json_str, int len, proto_msg_t *out) {
    memset(out, 0, sizeof(*out));
    out->type = PROTO_MSG_UNKNOWN;

    cJSON *root = cJSON_ParseWithLength(json_str, len);
    if (!root) return false;

    cJSON *type = cJSON_GetObjectItem(root, "type");
    if (!type || !cJSON_IsString(type)) { cJSON_Delete(root); return false; }

    const char *t = type->valuestring;
    if (strcmp(t, "welcome") == 0) {
        out->type = PROTO_MSG_WELCOME;
    } else if (strcmp(t, "transcript") == 0) {
        out->type = PROTO_MSG_TRANSCRIPT;
        cJSON *txt = cJSON_GetObjectItem(root, "text");
        if (txt && cJSON_IsString(txt))
            strncpy(out->text, txt->valuestring, sizeof(out->text) - 1);
    } else if (strcmp(t, "text_chunk") == 0) {
        out->type = PROTO_MSG_TEXT_CHUNK;
        cJSON *content = cJSON_GetObjectItem(root, "content");
        if (content && cJSON_IsString(content))
            strncpy(out->text, content->valuestring, sizeof(out->text) - 1);
    } else if (strcmp(t, "audio_chunk") == 0) {
        out->type = PROTO_MSG_AUDIO_CHUNK;
        cJSON *content = cJSON_GetObjectItem(root, "content");
        if (content && cJSON_IsString(content)) {
            out->content_len = strlen(content->valuestring);
            if (out->content_len < PROTO_BUF_SIZE)
                memcpy(out->content, content->valuestring, out->content_len);
        }
    } else if (strcmp(t, "audio_done") == 0) {
        out->type = PROTO_MSG_AUDIO_DONE;
    } else if (strcmp(t, "error") == 0) {
        out->type = PROTO_MSG_ERROR;
        cJSON *msg = cJSON_GetObjectItem(root, "message");
        if (msg && cJSON_IsString(msg))
            strncpy(out->text, msg->valuestring, sizeof(out->text) - 1);
    }

    cJSON_Delete(root);
    return true;
}
