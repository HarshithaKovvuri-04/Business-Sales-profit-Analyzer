import React from 'react'

export default function Card({children, className=''}){
  return (
    <div className={`p-4 rounded-xl bg-card shadow-soft glass ${className}`}>
      {children}
    </div>
  )
}
