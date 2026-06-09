<script setup lang="ts">
import { ref } from 'vue'
import { useModal } from '@/composables'
import { useUiStore } from '@/store'
import { apiService } from '@/services'
import { InfoTip } from '@/components/ui'

const { close } = useModal()
const ui = useUiStore()

const kbName = ref('')
const uploading = ref(false)
const selectedFile = ref<File | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)

function triggerFileInput() {
  fileInput.value?.click()
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    const file = input.files[0]
    if (file.size > 20 * 1024 * 1024) {
      ui.showToast('❌ 文件不能超过 20MB', 'error')
      input.value = ''
      return
    }
    selectedFile.value = file
  }
}

function onDragOver(e: DragEvent) {
  e.preventDefault()
}

function onDragDrop(e: DragEvent) {
  e.preventDefault()
  if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
    const file = e.dataTransfer.files[0]
    if (file.size > 20 * 1024 * 1024) {
      ui.showToast('❌ 文件不能超过 20MB', 'error')
      return
    }
    selectedFile.value = file
  }
}

async function confirmUpload() {
  if (!kbName.value.trim()) {
    ui.showToast('❌ 请输入知识库名称', 'error')
    return
  }
  if (!selectedFile.value) {
    ui.showToast('❌ 请选择一个文件', 'error')
    return
  }
  uploading.value = true
  try {
    await apiService.knowledge.upload(selectedFile.value, kbName.value.trim())
    ui.triggerKbRefresh()
    close()
    ui.showToast('📚 上传成功！')
  } catch (e) {
    ui.showToast(e instanceof Error ? e.message : '❌ 上传失败', 'error')
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div>
    <div class="mb-[18px]">
      <label class="block text-xs font-extrabold text-[var(--text2)] tracking-[.5px] uppercase mb-2">知识库名称</label>
      <input
        v-model="kbName"
        class="w-full p-[11px] border-[1.5px] border-[var(--border)] rounded-[var(--radius-sm)] text-sm text-[var(--text1)] bg-[var(--bg)] outline-none transition-all duration-200 focus:border-[var(--coral)] focus:shadow-[0_0_0_3px_rgba(255,107,107,.1)] focus:bg-white"
        placeholder="给这个知识库起个名字"
      />
    </div>

    <div class="mb-[18px]">
      <label class="block text-xs font-extrabold text-[var(--text2)] tracking-[.5px] uppercase mb-2">选择文件</label>
      <input
        ref="fileInput"
        type="file"
        accept=".pdf,.txt,.docx,.doc"
        class="hidden"
        @change="onFileChange"
      />
      <div
        class="border-2 border-dashed rounded-[var(--radius-md)] py-7 px-5 text-center cursor-pointer transition-all duration-200 bg-[var(--bg)]"
        :class="selectedFile
          ? 'border-[var(--teal)] bg-[#e8fdf5]'
          : 'border-[var(--border)] hover:border-[var(--indigo-lt)] hover:bg-[#eef0fc]'"
        @click="triggerFileInput"
        @dragover="onDragOver"
        @drop="onDragDrop"
      >
        <template v-if="selectedFile">
          <div class="text-[32px] mb-2">📄</div>
          <div class="text-sm font-bold text-[var(--text1)] mb-1">{{ selectedFile.name }}</div>
          <div class="text-xs text-[var(--text3)]">{{ (selectedFile.size / 1024).toFixed(1) }} KB</div>
          <button
            class="mt-2 text-xs font-bold text-[var(--coral)] bg-none border-none cursor-pointer"
            @click.stop="selectedFile = null; if (fileInput) fileInput.value = ''"
          >
            移除文件
          </button>
        </template>
        <template v-else>
          <div class="text-[32px] mb-2">📂</div>
          <div class="text-sm font-bold text-[var(--text2)] mb-1">点击选择文件，或拖放至此</div>
          <div class="text-xs text-[var(--text3)]">支持 PDF、TXT、DOCX，单文件最大 20MB</div>
        </template>
      </div>
    </div>

    <div class="flex gap-3 mt-6">
      <button
        class="flex-1 py-3 rounded-[var(--radius-sm)] bg-[var(--bg2)] text-[var(--text1)] border-none text-sm font-bold cursor-pointer transition-all duration-200 hover:bg-[var(--border)]"
        @click="close()"
      >
        取消
      </button>
      <button
        class="flex-1 py-3 rounded-[var(--radius-sm)] border-none text-sm font-extrabold cursor-pointer shadow-[0_3px_12px_rgba(255,107,107,.3)] transition-all duration-200 hover:-translate-y-px bg-gradient-to-br from-[var(--coral)] to-[#FF8E53] text-white disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0"
        :disabled="uploading"
        @click="confirmUpload"
      >
        {{ uploading ? '上传中…' : '确认上传' }}
      </button>
    </div>
  </div>
</template>
