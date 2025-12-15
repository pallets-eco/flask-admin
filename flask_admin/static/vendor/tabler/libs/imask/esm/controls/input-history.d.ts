import { type Selection } from '../core/utils';
export type InputHistoryState = {
    unmaskedValue: string;
    selection: Selection;
};
export default class InputHistory {
    static MAX_LENGTH: number;
    states: InputHistoryState[];
    currentIndex: number;
    get currentState(): InputHistoryState | undefined;
    get isEmpty(): boolean;
    push(state: InputHistoryState): void;
    go(steps: number): InputHistoryState | undefined;
    undo(): InputHistoryState | undefined;
    redo(): InputHistoryState | undefined;
    clear(): void;
}
//# sourceMappingURL=input-history.d.ts.map