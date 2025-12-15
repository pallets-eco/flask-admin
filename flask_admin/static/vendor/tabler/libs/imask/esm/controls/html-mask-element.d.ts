import MaskElement, { EventHandlers } from './mask-element';
/** Bridge between HTMLElement and {@link Masked} */
export default abstract class HTMLMaskElement extends MaskElement {
    /** HTMLElement to use mask on */
    input: HTMLElement;
    _handlers: EventHandlers;
    abstract value: string;
    constructor(input: HTMLElement);
    get rootElement(): HTMLDocument;
    /** Is element in focus */
    get isActive(): boolean;
    /** Binds HTMLElement events to mask internal events */
    bindEvents(handlers: EventHandlers): void;
    _onKeydown(e: KeyboardEvent): void;
    _onBeforeinput(e: InputEvent): void;
    _onCompositionEnd(e: CompositionEvent): void;
    _onInput(e: InputEvent): void;
    /** Unbinds HTMLElement events to mask internal events */
    unbindEvents(): void;
}
//# sourceMappingURL=html-mask-element.d.ts.map