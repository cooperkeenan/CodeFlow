import SymbolList from './SymbolList'

export default function MethodList({ methods, onSelect, selectedFqn }) {
  return <SymbolList heading="Methods" items={methods} attr="data-method" onSelect={onSelect} selectedFqn={selectedFqn} />
}
