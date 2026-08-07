import SymbolList from './SymbolList'

export default function HelperList({ helpers, onSelect, selectedFqn }) {
  return <SymbolList heading="Uses" items={helpers} attr="data-helper" onSelect={onSelect} selectedFqn={selectedFqn} />
}
