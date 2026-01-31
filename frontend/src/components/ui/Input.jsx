import React from 'react'

export default function Input({label, icon, className='', ...props}){
  if(!icon){
    return (
      <label className="flex flex-col text-sm gap-1">
        {label && <span className="text-slate-600">{label}</span>}
        <input className={`px-3 py-2 rounded-lg border border-slate-200 bg-transparent focus:outline-none focus:ring-2 focus:ring-fintech-accent/30 ${className}`} {...props} />
      </label>
    )
  }

  return (
    <label className="flex flex-col text-sm gap-1 relative">
      {label && <span className="text-slate-600">{label}</span>}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
          {icon}
        </div>
        <input className={`pl-10 pr-3 py-2 rounded-lg border border-slate-200 bg-transparent w-full focus:outline-none focus:ring-2 focus:ring-fintech-accent/30 ${className}`} {...props} />
      </div>
    </label>
  )
}
