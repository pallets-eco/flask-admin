export type ElementEvent = 'selectionChange' | 'input' | 'drop' | 'click' | 'focus' | 'commit';
export type EventHandlers = {
    [key in ElementEvent]: (...args: any[]) => void;
} & {
    undo?: (...args: any[]) => void;
    redo?: (...args: any[]) => void;
};
/**  Generic element API to use with mask */
export default abstract class MaskElement {
    /** */
    abstract _unsafeSelectionStart: number | null;
    /** */
    abstract _unsafeSelectionEnd: number | null;
    /** */
    abstract value: string;
    /** Safely returns selection start */
    get selectionStart(): number;
    /** Safely returns selection end */
    get selectionEnd(): number;
    /** Safely sets element selection */
    select(start: number, end: number): void;
    /** */
    get isActive(): boolean;
    /** */
    abstract _unsafeSelect(start: number, end: number): void;
    /** */
    abstract bindEvents(handlers: EventHandlers): void;
    /** */
    abstract unbindEvents(): void;
}
//# sourceMappingURL=mask-element.d.ts.map