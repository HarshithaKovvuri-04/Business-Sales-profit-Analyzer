import React from 'react'

export default function Input({label, ...props}){
  return (
    <label className="flex flex-col text-sm gap-1">
      {label && <span className="text-slate-600">{label}</span>}
      <input className="px-3 py-2 rounded-md border border-slate-200 bg-transparent" {...props} />
    </label>
  )
}
