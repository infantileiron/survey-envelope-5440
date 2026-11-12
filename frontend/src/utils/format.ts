export const num=(v:number|null|undefined,d=2)=>v===null||v===undefined?'—':Number.isFinite(v)?v.toFixed(d):'不可估计';
export const pct=(v:number|null)=>v===null?'不可估计（分母0）':num(v*100,1)+'%';
export const short=(s:string)=>s.slice(0,12);
