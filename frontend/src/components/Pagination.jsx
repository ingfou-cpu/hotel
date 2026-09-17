// Pagination.jsx — Pagination avec infos
// Props: page (1-based), pageCount, total, onChange(page), className, showInfo?, showPageSize?, pageSize?, onPageSizeChange?
import React, { useMemo } from 'react'

export default function Pagination({
  page = 1,
  pageCount = 1,
  total = 0,
  onChange,
  className = '',
  showInfo = true,
  showPageSize = false,
  pageSize,
  onPageSizeChange
}) {
  const pages = useMemo(() => {
    if (pageCount <= 7) {
      return Array.from({ length: pageCount }, (_, i) => i + 1)
    }
    const pages = [1]
    if (page > 3) pages.push('...')
    const start = Math.max(2, page - 1)
    const end = Math.min(pageCount - 1, page + 1)
    for (let i = start; i <= end; i++) pages.push(i)
    if (page < pageCount - 2) pages.push('...')
    pages.push(pageCount)
    return pages
  }, [page, pageCount])

  return (
    <nav className={`pagination ${className}`} aria-label="Pagination">
      {showInfo && total > 0 && (
        <span className="pagination-info">
          Page {page} sur {pageCount} — {total} résultat{total > 1 ? 's' : ''}
        </span>
      )}
      <button
        className="pagination-btn"
        onClick={() => onChange(page - 1)}
        disabled={page <= 1}
        aria-label="Page précédente"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <path d="M10 8L6 12V4L10 8Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
      {pages.map((p, i) =>
        p === '...' ? (
          <span key={`ellipsis-${i}`} className="pagination-ellipsis">…</span>
        ) : (
          <button
            key={p}
            className={`pagination-btn ${p === page ? 'active' : ''}`}
            onClick={() => onChange(p)}
            aria-label={`Page ${p}`}
            aria-current={p === page ? 'page' : undefined}
          >
            {p}
          </button>
        )
      )}
      <button
        className="pagination-btn"
        onClick={() => onChange(page + 1)}
        disabled={page >= pageCount}
        aria-label="Page suivante"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <path d="M6 8L10 12V4L6 8Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
      {showPageSize && pageSize && onPageSizeChange && (
        <div style={{ marginLeft: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <label htmlFor="page-size" className="text-sm text-gray-500">Par page :</label>
          <select
            id="page-size"
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            className="field-input field-input-sm"
            style={{ width: 'auto', padding: '0.25rem 2rem 0.25rem 0.5rem' }}
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </div>
      )}
    </nav>
  )
}