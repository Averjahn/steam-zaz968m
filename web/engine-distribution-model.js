// Functional four-valve distribution. These are commanded states, not a solved
// mechanical cam/actuator or a calibrated steam-flow model.
export const valveEdges=Object.freeze([
 {id:'PA',from:'P',to:'A',chamber:'A',kind:'inlet'},
 {id:'AT',from:'A',to:'T',chamber:'A',kind:'exhaust'},
 {id:'PB',from:'P',to:'B',chamber:'B',kind:'inlet'},
 {id:'BT',from:'B',to:'T',chamber:'B',kind:'exhaust'}
].map(Object.freeze));
export function distributionState(pose){
 const valves=valveEdges.map(e=>({...e,open:Boolean(pose[e.chamber][e.kind])}));
 const adjacency=new Map(['P','A','B','T'].map(n=>[n,[]]));
 for(const e of valves)if(e.open){adjacency.get(e.from).push(e.to);adjacency.get(e.to).push(e.from);}
 const reached=new Set(['P']),pending=['P'];
 while(pending.length)for(const n of adjacency.get(pending.pop()))if(!reached.has(n)){reached.add(n);pending.push(n);}
 const overlap=['A','B'].filter(ch=>pose[ch].inlet&&pose[ch].exhaust);
 return {valves,shortCircuit:reached.has('T'),overlap,valid:!reached.has('T')&&!overlap.length};
}
export function tubeVolumeCm3(length_mm,inside_mm){
 if(!Number.isFinite(length_mm)||length_mm<0||!Number.isFinite(inside_mm)||inside_mm<=0)throw RangeError('Invalid tube dimensions');
 return Math.PI*inside_mm**2/4*length_mm/1000;
}
