import { computed, type Ref } from 'vue'

interface FormField<T> {
  value: T
  validate: (value: T) => string | true
}

export function useFormValidator<T extends Record<string, FormField<unknown>>>(
  fields: Ref<T>,
) {
  const errors = computed(() => {
    const errs: Partial<Record<keyof T, string>> = {}
    for (const key of Object.keys(fields.value) as (keyof T)[]) {
      const result = (fields.value[key] as FormField<unknown>).validate(
        fields.value[key].value,
      )
      if (result !== true) errs[key] = result
    }
    return errs
  })

  const isValid = computed(() => Object.keys(errors.value).length === 0)

  function validateAll(): boolean {
    return isValid.value
  }

  function reset() {
    for (const key of Object.keys(fields.value)) {
      ;(fields.value[key] as FormField<unknown>).value = ''
    }
  }

  return { errors, isValid, validateAll, reset }
}

export function required(msg = '此项为必填'): (value: unknown) => string | true {
  return (value: unknown) => {
    if (typeof value === 'string' && value.trim().length === 0) return msg
    if (value === null || value === undefined) return msg
    return true
  }
}

export function minLength(
  n: number,
  msg?: string,
): (value: unknown) => string | true {
  return (value: unknown) => {
    if (typeof value === 'string' && value.trim().length < n) {
      return msg ?? `至少需要 ${n} 个字符`
    }
    return true
  }
}

export function numeric(msg = '只允许数字'): (value: unknown) => string | true {
  return (value: unknown) => {
    if (typeof value === 'string' && value.length > 0 && !/^\d+$/.test(value)) {
      return msg
    }
    return true
  }
}
