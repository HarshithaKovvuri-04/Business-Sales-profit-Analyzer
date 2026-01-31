import React from 'react'

export default function Button({children, variant='primary', className='', ...props}){
  const base = 'px-4 py-2 rounded-lg font-medium transition-transform active:scale-95 inline-flex items-center justify-center gap-2 '
  const variants = {
    primary: 'bg-fintech-accent text-white hover:bg-fintech-accent2',
    success: 'bg-fintech-success text-white',
    danger: 'bg-fintech-danger text-white',
    ghost: 'bg-transparent border border-slate-200 text-slate-700'
  }
  const v = variants[variant] || variants.primary
  return <button className={`${base} ${v} ${className}`} {...props}>{children}</button>
}
