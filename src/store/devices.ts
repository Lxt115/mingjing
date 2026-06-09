import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Device } from '@/types'
import { apiService } from '@/services'

export const useDevicesStore = defineStore('devices', () => {
  const devices = ref<Device[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const onlineDevices = computed(() =>
    devices.value.filter((d) => d.status === 'online'),
  )

  const offlineDevices = computed(() =>
    devices.value.filter((d) => d.status === 'offline'),
  )

  async function fetchDevices() {
    loading.value = true
    error.value = null
    try {
      const res = await apiService.devices.getList()
      devices.value = res.data
    } catch (e) {
      error.value = e instanceof Error ? e.message : '获取设备列表失败'
    } finally {
      loading.value = false
    }
  }

  async function bindDevice(code: string, agentId?: string) {
    loading.value = true
    error.value = null
    try {
      const res = await apiService.devices.bind(code, agentId)
      devices.value.push(res.data)
      return res.data
    } catch (e) {
      error.value = e instanceof Error ? e.message : '设备绑定失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function unbindDevice(id: string) {
    loading.value = true
    error.value = null
    try {
      await apiService.devices.unbind(id)
      devices.value = devices.value.filter((d) => d.id !== id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : '设备解绑失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function upgradeFirmware(id: string) {
    loading.value = true
    error.value = null
    try {
      const res = await apiService.devices.upgradeFirmware(id)
      const idx = devices.value.findIndex((d) => d.id === id)
      if (idx !== -1) devices.value[idx] = res.data
      return res.data
    } catch (e) {
      error.value = e instanceof Error ? e.message : '固件升级失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function assignRole(id: string, agentId: string | null) {
    loading.value = true
    error.value = null
    try {
      const res = await apiService.devices.assignRole(id, agentId)
      const idx = devices.value.findIndex((d) => d.id === id)
      if (idx !== -1) devices.value[idx] = res.data
      return res.data
    } catch (e) {
      error.value = e instanceof Error ? e.message : '角色分配失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  function toggleAutoUpgrade(id: string) {
    const device = devices.value.find((d) => d.id === id)
    if (device) {
      device.autoUpgrade = !device.autoUpgrade
    }
  }

  function getDevicesByAgent(agentId: string) {
    return devices.value.filter((d) => d.boundAgentId === agentId)
  }

  function clearError() {
    error.value = null
  }

  return {
    devices,
    loading,
    error,
    onlineDevices,
    offlineDevices,
    fetchDevices,
    bindDevice,
    unbindDevice,
    upgradeFirmware,
    assignRole,
    toggleAutoUpgrade,
    getDevicesByAgent,
    clearError,
  }
})
