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

async function confirmUpload() {
  if (!kbName.value.trim()) {
    ui.showToast('❌ 请输入知识库名称', 'error')
    return
  }
  uploading.value = true
  try {
    await apiService.knowledge.upload(new File([], 'placeholder.txt'), kbName.value.trim())
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
      <div
        class="border-2 border-dashed border-[var(--border)] rounded-[var(--radius-md)] py-7 px-5 text-center cursor-pointer transition-all duration-200 bg-[var(--bg)] hover:border-[var(--indigo-lt)] hover:bg-[#eef0fc]"
        @click="ui.showToast('文件选择功能开发中…')"
      >
        <div class="text-[32px] mb-2">📂</div>
        <div class="text-sm font-bold text-[var(--text2)] mb-1">点击选择文件，或拖放至此</div>
        <div class="text-xs text-[var(--text3)]">支持 PDF、TXT、DOCX，单文件最大 20MB</div>
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
        class="flex-1 py-3 rounded-[var(--radius-sm)] border-none text-sm font-extrabold cursor-pointer shadow-[0_3px_12px_rgba(255,107,107,.3)] transition-all duration-200 hover:-translate-y-px bg-gradient-to-br from-[var(--coral)] to-[#FF8E53] text-white"
        :disabled="uploading"
        @click="confirmUpload"
      >
        {{ uploading ? '上传中…' : '确认上传' }}
      </button>
    </div>
  </div>
</template>
