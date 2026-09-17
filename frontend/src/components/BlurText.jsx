import React, { useEffect, useRef, useState } from 'react'

// BlurText — word-by-word entrance: blur(10px) opacity 0 y 50 -> blur(0)/opacity 1, ~0.7s, staggered ~100ms, triggered at 10% visibility
export default function BlurText({ text = '', as: Tag = 'h1', className = '', style, delay = 100, duration = 700, italicWord = null }) {
  const ref = useRef(null)
  const [visible, setVisible] = useState(false)
  const words = text.split(' ')

  useEffect(() => {
    if (typeof window === 'undefined') return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setVisible(true)
      return
    }
    const el = ref.current
    if (!el) return
    const obs = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true)
          obs.disconnect()
        }
      },
      { threshold: 0.1 }
    )
    obs.observe(el)
    return () => obs.disconnect()
  }, [])

  return (
    <Tag ref={ref} className={className} style={style} aria-label={text}>
      {words.map((w, i) => {
        const isItalic = italicWord != null && w.toLowerCase().replace(/[.,!?;:]/g,'') === italicWord.toLowerCase()
        const d = visible ? i * delay : 0
        return (
          <span
            key={`${w}-${i}`}
            className="blur-text-word"
            style={{
              filter: visible ? 'blur(0px)' : 'blur(10px)',
              opacity: visible ? 1 : 0,
              transform: visible ? 'translateY(0)' : 'translateY(50px)',
              transition: `filter ${duration}ms cubic-bezier(0.2,0.8,0.2,1) ${d}ms, opacity ${duration}ms ease ${d}ms, transform ${duration}ms cubic-bezier(0.2,0.8,0.2,1) ${d}ms`,
              fontStyle: isItalic ? 'italic' : undefined,
              color: isItalic ? 'var(--color-accent)' : undefined,
            }}
          >
            {w}
            {i < words.length - 1 ? '\u00A0' : ''}
          </span>
        )
      })}
    </Tag>
  )
}
