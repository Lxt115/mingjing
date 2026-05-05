import { ref, onMounted, onUnmounted } from 'vue'

const BREAKPOINT = 768

const isMobile = ref(false)

function check() {
  isMobile.value = window.innerWidth < BREAKPOINT
}

export function useMediaQuery() {
  onMounted(() => {
    check()
    window.addEventListener('resize', check)
  })
  onUnmounted(() => {
    window.removeEventListener('resize', check)
  })

  return { isMobile }
}
