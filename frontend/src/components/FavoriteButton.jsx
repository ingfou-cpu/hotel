// FavoriteButton.jsx — Bouton favori (cœur)
import React from 'react'

export default function FavoriteButton({ isFavorite, onToggle, disabled = false, size = 'md', className = '', ariaLabel }) {
  const label = ariaLabel || (isFavorite ? 'Retirer des favoris' : 'Ajouter aux favoris')
  const sizePx = size === 'sm' ? 18 : size === 'lg' ? 24 : 20
  return (
    <button
      type="button"
      className={`${className}`}
      onClick={onToggle}
      disabled={disabled}
      aria-label={label}
      aria-pressed={isFavorite}
      style={{
        width: sizePx + 16,
        height: sizePx + 16,
        borderRadius: '50%',
        display: 'grid',
        placeItems: 'center',
        background: isFavorite ? 'rgba(232,107,107,0.16)' : 'rgba(255,255,255,0.08)',
        border: `1px solid ${isFavorite ? 'rgba(232,107,107,0.30)' : 'rgba(255,255,255,0.12)'}`,
        color: isFavorite ? '#FF9B9B' : 'rgba(255,255,255,0.72)',
        boxShadow: '0 4px 16px rgba(0,0,0,0.22)',
        opacity: disabled ? 0.5 : 1,
        cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'all 180ms ease',
      }}
    >
      <svg width={sizePx} height={sizePx} viewBox="0 0 24 24" fill={isFavorite ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth={isFavorite ? 0 : 1.8} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
      </svg>
    </button>
  )
}
