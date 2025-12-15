import ChangeDetails from '../core/change-details';
import { type AppendFlags } from './base';
import { type FactoryArg, type ExtendFactoryArgOptions, type UpdateOpts } from './factory';
import MaskedPattern, { type BlockExtraOptions, type MaskedPatternState } from './pattern';
import type PatternBlock from './pattern/block';
export type RepeatBlockExtraOptions = Pick<BlockExtraOptions, 'repeat'>;
export type RepeatBlockOptions = ExtendFactoryArgOptions<RepeatBlockExtraOptions>;
/** Pattern mask */
export default class RepeatBlock<M extends FactoryArg> extends MaskedPattern {
    _blockOpts: M & {
        repeat?: number;
    };
    repeat: Required<RepeatBlockExtraOptions>['repeat'];
    get repeatFrom(): number;
    get repeatTo(): number;
    constructor(opts: RepeatBlockOptions);
    updateOptions(opts: UpdateOpts<RepeatBlockOptions>): void;
    _update(opts: UpdateOpts<M> & RepeatBlockExtraOptions): void;
    _allocateBlock(bi: number): PatternBlock | undefined;
    _appendCharRaw(ch: string, flags?: AppendFlags<MaskedPatternState>): ChangeDetails;
    _trimEmptyTail(fromPos?: number, toPos?: number): void;
    reset(): void;
    remove(fromPos?: number, toPos?: number): ChangeDetails;
    totalInputPositions(fromPos?: number, toPos?: number): number;
    get state(): MaskedPatternState;
    set state(state: MaskedPatternState);
}
//# sourceMappingURL=repeat.d.ts.map