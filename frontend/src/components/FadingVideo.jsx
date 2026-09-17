import React, { useEffect, useRef, useState } from 'react'

// FadingVideo — rAF crossfade loop, no CSS transitions on video opacity
// Spec: starts opacity 0; fade to 1 on loadeddata; when ~0.55s before end, fade out; on ended reset to 0 and play again
// Reduced-motion: poster image instead
export default function FadingVideo({ src, poster, className = '', style, muted = true, loop = true, playsInline = true, autoPlay = true }) {
  const videoRef = useRef(null)
  const rafRef = useRef(null)
  const [prefersReduced, setPrefersReduced] = useState(false)
  const [opacity, setOpacity] = useState(0)

  useEffect(() => {
    const m = window.matchMedia('(prefers-reduced-motion: reduce)')
    setPrefersReduced(m.matches)
    const onChange = (e) => setPrefersReduced(e.matches)
    m.addEventListener ? m.addEventListener('change', onChange) : m.addListener(onChange)
    return () => { m.removeEventListener ? m.removeEventListener('change', onChange) : m.removeListener(onChange) }
  }, [])

  useEffect(() => {
    if (prefersReduced) return
    const v = videoRef.current
    if (!v) return

    let target = 0
    let current = 0
    let animating = false

    const lerp = (a, b, t) => a + (b - a) * t

    const tick = () => {
      // ease towards target at ~12% per frame
      current = lerp(current, target, 0.12)
      if (Math.abs(target - current) < 0.01) current = target
      setOpacity(current)
      if (current !== target) {
        rafRef.current = requestAnimationFrame(tick)
        animating = true
      } else {
        animating = false
      }
    }
    const ensureTick = () => { if (!animating) { animating = true; rafRef.current = requestAnimationFrame(tick) } }

    const onLoaded = () => {
      target = 1
      ensureTick()
      // ensure playing
      v.play().catch(() => {})
    }
    const onTimeUpdate = () => {
      if (!v.duration || Number.isNaN(v.duration)) return
      const remain = v.duration - v.currentTime
      if (remain <= 0.55 && target !== 0) {
        target = 0
        ensureTick()
      } else if (remain > 0.65 && target === 0 && v.currentTime < 0.5) {
        // just looped via ended handler — fade in
      }
    }
    const onEnded = () => {
      v.currentTime = 0
      target = 1
      setOpacity(0)
      current = 0
      ensureTick()
      v.play().catch(() => {})
    }

    // if already have data
    if (v.readyState >= 2) onLoaded()

    v.addEventListener('loadeddata', onLoaded)
    v.addEventListener('timeupdate', onTimeUpdate)
    v.addEventListener('ended', onEnded)

    return () => {
      v.removeEventListener('loadeddata', onLoaded)
      v.removeEventListener('timeupdate', onTimeUpdate)
      v.removeEventListener('ended', onEnded)
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
  }, [prefersReduced, src])

  if (prefersReduced) {
    return <img src={poster} alt="" className={className} style={style} loading="eager" />
  }

  return (
    <video
      ref={videoRef}
      className={className}
      style={{ ...style, opacity, transition: 'none' }}
      autoPlay={autoPlay}
      muted={muted}
      loop={false}
      playsInline={playsInline}
      preload="auto"
      poster={poster}
    >
      <source src={src} type="video/mp4" />
    </video>
  )
}
