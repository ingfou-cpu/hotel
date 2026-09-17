// StarRating.jsx — Affichage/interaction notation étoiles
// Props: value (0-5), max=5, size='sm'|'md'|'lg', interactive?, onChange?, showValue?, className, readonly?
import React, { useState } from 'react'

const sizeClasses = {
  sm: 'w-4 h-4',
  md: 'w-5 h-5',
  lg: 'w-6 h-6'
}

const StarIcon = ({ filled, hover, sizeClass }) => (
  <svg
    className={`star-rating-star ${sizeClass} ${filled ? 'filled' : ''} ${hover ? 'hover' : ''}`}
    viewBox="0 0 20 20"
    fill="currentColor"
    aria-hidden="true"
  >
    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
  </svg>
)

export default function StarRating({
  value = 0,
  max = 5,
  size = 'md',
  interactive = false,
  onChange,
  showValue = false,
  className = '',
  readonly = false
}) {
  const [hoverValue, setHoverValue] = useState(0)
  const displayValue = interactive && hoverValue > 0 ? hoverValue : value
  const sizeClass = sizeClasses[size] || sizeClasses.md

  const handleClick = (starValue) => {
    if (interactive && !readonly && onChange) {
      onChange(starValue)
    }
  }

  const handleKeyDown = (e, starValue) => {
    if (!interactive || readonly) return
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      onChange?.(starValue)
    } else if (e.key === 'ArrowRight' && starValue < max) {
      e.preventDefault()
      onChange?.(starValue + 1)
    } else if (e.key === 'ArrowLeft' && starValue > 1) {
      e.preventDefault()
      onChange?.(starValue - 1)
    }
  }

  return (
    <div className={`star-rating ${className}`} role={interactive && !readonly ? 'radiogroup' : 'img'} aria-label={`Note : ${value} sur ${max}`} aria-readonly={readonly || !interactive}>
      {Array.from({ length: max }, (_, i) => i + 1).map((star) => (
        <StarIcon
          key={star}
          filled={star <= displayValue}
          hover={interactive && !readonly && star <= hoverValue && hoverValue > 0}
          sizeClass={sizeClass}
        />
      ))}
      {interactive && !readonly && (
        <>
          {Array.from({ length: max }, (_, i) => i + 1).map((star) => (
            <button
              key={`btn-${star}`}
              type="button"
              className="absolute inset-0 opacity-0 focus:opacity-100"
              style={{ position: 'absolute', width: sizeClass.replace('w-', '').replace('h-', ''), height: sizeClass.replace('w-', '').replace('h-', '') }}
              onClick={() => handleClick(star)}
              onMouseEnter={() => setHoverValue(star)}
              onMouseLeave={() => setHoverValue(0)}
              onKeyDown={(e) => handleKeyDown(e, star)}
              aria-label={`${star} étoile${star > 1 ? 's' : ''}`}
              aria-checked={star <= value}
              tabIndex={star === Math.round(value) || star === 1 ? 0 : -1}
            />
          ))}
        </>
      )}
      {showValue && (
        <span className="ml-2 text-sm font-medium text-gray-700" aria-hidden="true">
          {displayValue.toFixed(1)} / {max}
        </span>
      )}
    </div>
  )
}