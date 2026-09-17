// Table.jsx — Tableau responsive
// Props: columns=[{key, label, render?(row), className?, align='left'|'center'|'right'}], rows=[], emptyMessage, className, striped?, hoverable?
import React from 'react'

export default function Table({ columns = [], rows = [], emptyMessage = 'Aucune donnée', className = '', striped = false, hoverable = true }) {
  return (
    <div className={`table-wrapper ${className}`}>
      {rows.length > 0 ? (
        <table className="table" role="grid">
          <thead>
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  scope="col"
                  style={{
                    textAlign: col.align || 'left',
                    width: col.width
                  }}
                  className={col.headerClassName}
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={row.id || rowIndex} style={{ ...(striped && rowIndex % 2 === 1 ? { background: 'var(--color-bg-secondary)' } : {}) }}>
                {columns.map((col) => (
                  <td
                    key={col.key}
                    style={{ textAlign: col.align || 'left' }}
                    className={col.cellClassName}
                  >
                    {col.render ? col.render(row, rowIndex) : row[col.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className="empty-state" style={{ padding: '2rem', border: 'none' }}>
          <p className="empty-state-title">{emptyMessage}</p>
        </div>
      )}
    </div>
  )
}