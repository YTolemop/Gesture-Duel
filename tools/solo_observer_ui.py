from pathlib import Path
p=Path(__file__).resolve().parents[1]/'gesture-arena/apps/web/src/solo-draft.tsx'
s=p.read_text(encoding='utf-8')
s=s.replace('  useEffect(()=>{setCategory(slots.find(s=>!me.loadout[s])', '  const filled=(s:string)=>s==="ultimate"?me.ultimatePicked:!!me.loadout[s];\n  useEffect(()=>{setCategory(slots.find(s=>!filled(s))')
s=s.replace('me.loadout[s]?"locked":""','filled(s)?"locked":""').replace('me.loadout[s]?"✓":"＋"','filled(s)?"✓":"＋"').replace('?.name??"尚未選擇"','?.name??(filled(s)?"已鎖定":"尚未選擇")')
s=s.replace('disabled={!!me.loadout[s]}','disabled={filled(s)}').replace('me.loadout[s]?" ✓":""','filled(s)?" ✓":""').replace('disabled={pending||!!me.loadout[skill.slot]}','disabled={readOnly||pending||filled(skill.slot)}')
p.write_text(s,encoding='utf-8')
