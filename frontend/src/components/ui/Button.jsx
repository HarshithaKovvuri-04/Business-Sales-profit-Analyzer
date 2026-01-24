import React from 'react'

export default function Button({children, variant='primary', className='', ...props}){
  const base = 'px-4 py-2 rounded-md font-medium transition-transform active:scale-95 '
  const variants = {
    primary: 'bg-indigo-600 text-white hover:bg-indigo-700',
    ghost: 'bg-transparent border border-slate-200'
  }
  return <button className={base + (variants[variant]||variants.primary) + ' ' + className} {...props}>{children}</button>
}
