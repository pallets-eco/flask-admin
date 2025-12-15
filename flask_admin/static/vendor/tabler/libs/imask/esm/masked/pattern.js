import ChangeDetails from '../core/change-details.js';
import IMask from '../core/holder.js';
import { DIRECTION } from '../core/utils.js';
import Masked from './base.js';
import createMask, { normalizeOpts } from './factory.js';
import ChunksTailDetails from './pattern/chunk-tail-details.js';
import PatternCursor from './pattern/cursor.js';
import PatternFixedDefinition from './pattern/fixed-definition.js';
import PatternInputDefinition from './pattern/input-definition.js';
import './regexp.js';
import '../core/continuous-tail-details.js';

/** Pattern mask */
class MaskedPattern extends Masked {
  /** */

  /** */

  /** Single char for empty input */

  /** Single char for filled input */

  /** Show placeholder only when needed */

  /** Enable characters overwriting */

  /** */

  /** */

  /** */

  constructor(opts) {
    super({
      ...MaskedPattern.DEFAULTS,
      ...opts,
      definitions: Object.assign({}, PatternInputDefinition.DEFAULT_DEFINITIONS, opts == null ? void 0 : opts.definitions)
    });
  }
  updateOptions(opts) {
    super.updateOptions(opts);
  }
  _update(opts) {
    opts.definitions = Object.assign({}, this.definitions, opts.definitions);
    super._update(opts);
    this._rebuildMask();
  }
  _rebuildMask() {
    const defs = this.definitions;
    this._blocks = [];
    this.exposeBlock = undefined;
    this._stops = [];
    this._maskedBlocks = {};
    const pattern = this.mask;
    if (!pattern || !defs) return;
    let unmaskingBlock = false;
    let optionalBlock = false;
    for (let i = 0; i < pattern.length; ++i) {
      if (this.blocks) {
        const p = pattern.slice(i);
        const bNames = Object.keys(this.blocks).filter(bName => p.indexOf(bName) === 0);
        // order by key length
        bNames.sort((a, b) => b.length - a.length);
        // use block name with max length
        const bName = bNames[0];
        if (bName) {
          const {
            expose,
            repeat,
            ...bOpts
          } = normalizeOpts(this.blocks[bName]); // TODO type Opts<Arg & Extra>
          const blockOpts = {
            lazy: this.lazy,
            eager: this.eager,
            placeholderChar: this.placeholderChar,
            displayChar: this.displayChar,
            overwrite: this.overwrite,
            autofix: this.autofix,
            ...bOpts,
            repeat,
            parent: this
          };
          const maskedBlock = repeat != null ? new IMask.RepeatBlock(blockOpts /* TODO */) : createMask(blockOpts);
          if (maskedBlock) {
            this._blocks.push(maskedBlock);
            if (expose) this.exposeBlock = maskedBlock;

            // store block index
            if (!this._maskedBlocks[bName]) this._maskedBlocks[bName] = [];
            this._maskedBlocks[bName].push(this._blocks.length - 1);
          }
          i += bName.length - 1;
          continue;
        }
      }
      let char = pattern[i];
      let isInput = (char in defs);
      if (char === MaskedPattern.STOP_CHAR) {
        this._stops.push(this._blocks.length);
        continue;
      }
      if (char === '{' || char === '}') {
        unmaskingBlock = !unmaskingBlock;
        continue;
      }
      if (char === '[' || char === ']') {
        optionalBlock = !optionalBlock;
        continue;
      }
      if (char === MaskedPattern.ESCAPE_CHAR) {
        ++i;
        char = pattern[i];
        if (!char) break;
        isInput = false;
      }
      const def = isInput ? new PatternInputDefinition({
        isOptional: optionalBlock,
        lazy: this.lazy,
        eager: this.eager,
        placeholderChar: this.placeholderChar,
        displayChar: this.displayChar,
        ...normalizeOpts(defs[char]),
        parent: this
      }) : new PatternFixedDefinition({
        char,
        eager: this.eager,
        isUnmasking: unmaskingBlock
      });
      this._blocks.push(def);
    }
  }
  get state() {
    return {
      ...super.state,
      _blocks: this._blocks.map(b => b.state)
    };
  }
  set state(state) {
    if (!state) {
      this.reset();
      return;
    }
    const {
      _blocks,
      ...maskedState
    } = state;
    this._blocks.forEach((b, bi) => b.state = _blocks[bi]);
    super.state = maskedState;
  }
  reset() {
    super.reset();
    this._blocks.forEach(b => b.reset());
  }
  get isComplete() {
    return this.exposeBlock ? this.exposeBlock.isComplete : this._blocks.every(b => b.isComplete);
  }
  get isFilled() {
    return this._blocks.every(b => b.isFilled);
  }
  get isFixed() {
    return this._blocks.every(b => b.isFixed);
  }
  get isOptional() {
    return this._blocks.every(b => b.isOptional);
  }
  doCommit() {
    this._blocks.forEach(b => b.doCommit());
    super.doCommit();
  }
  get unmaskedValue() {
    return this.exposeBlock ? this.exposeBlock.unmaskedValue : this._blocks.reduce((str, b) => str += b.unmaskedValue, '');
  }
  set unmaskedValue(unmaskedValue) {
    if (this.exposeBlock) {
      const tail = this.extractTail(this._blockStartPos(this._blocks.indexOf(this.exposeBlock)) + this.exposeBlock.displayValue.length);
      this.exposeBlock.unmaskedValue = unmaskedValue;
      this.appendTail(tail);
      this.doCommit();
    } else super.unmaskedValue = unmaskedValue;
  }
  get value() {
    return this.exposeBlock ? this.exposeBlock.value :
    // TODO return _value when not in change?
    this._blocks.reduce((str, b) => str += b.value, '');
  }
  set value(value) {
    if (this.exposeBlock) {
      const tail = this.extractTail(this._blockStartPos(this._blocks.indexOf(this.exposeBlock)) + this.exposeBlock.displayValue.length);
      this.exposeBlock.value = value;
      this.appendTail(tail);
      this.doCommit();
    } else super.value = value;
  }
  get typedValue() {
    return this.exposeBlock ? this.exposeBlock.typedValue : super.typedValue;
  }
  set typedValue(value) {
    if (this.exposeBlock) {
      const tail = this.extractTail(this._blockStartPos(this._blocks.indexOf(this.exposeBlock)) + this.exposeBlock.displayValue.length);
      this.exposeBlock.typedValue = value;
      this.appendTail(tail);
      this.doCommit();
    } else super.typedValue = value;
  }
  get displayValue() {
    return this._blocks.reduce((str, b) => str += b.displayValue, '');
  }
  appendTail(tail) {
    return super.appendTail(tail).aggregate(this._appendPlaceholder());
  }
  _appendEager() {
    var _this$_mapPosToBlock;
    const details = new ChangeDetails();
    let startBlockIndex = (_this$_mapPosToBlock = this._mapPosToBlock(this.displayValue.length)) == null ? void 0 : _this$_mapPosToBlock.index;
    if (startBlockIndex == null) return details;

    // TODO test if it works for nested pattern masks
    if (this._blocks[startBlockIndex].isFilled) ++startBlockIndex;
    for (let bi = startBlockIndex; bi < this._blocks.length; ++bi) {
      const d = this._blocks[bi]._appendEager();
      if (!d.inserted) break;
      details.aggregate(d);
    }
    return details;
  }
  _appendCharRaw(ch, flags) {
    if (flags === void 0) {
      flags = {};
    }
    const blockIter = this._mapPosToBlock(this.displayValue.length);
    const details = new ChangeDetails();
    if (!blockIter) return details;
    for (let bi = blockIter.index, block; block = this._blocks[bi]; ++bi) {
      var _flags$_beforeTailSta;
      const blockDetails = block._appendChar(ch, {
        ...flags,
        _beforeTailState: (_flags$_beforeTailSta = flags._beforeTailState) == null || (_flags$_beforeTailSta = _flags$_beforeTailSta._blocks) == null ? void 0 : _flags$_beforeTailSta[bi]
      });
      details.aggregate(blockDetails);
      if (blockDetails.consumed) break; // go next char
    }
    return details;
  }
  extractTail(fromPos, toPos) {
    if (fromPos === void 0) {
      fromPos = 0;
    }
    if (toPos === void 0) {
      toPos = this.displayValue.length;
    }
    const chunkTail = new ChunksTailDetails();
    if (fromPos === toPos) return chunkTail;
    this._forEachBlocksInRange(fromPos, toPos, (b, bi, bFromPos, bToPos) => {
      const blockChunk = b.extractTail(bFromPos, bToPos);
      blockChunk.stop = this._findStopBefore(bi);
      blockChunk.from = this._blockStartPos(bi);
      if (blockChunk instanceof ChunksTailDetails) blockChunk.blockIndex = bi;
      chunkTail.extend(blockChunk);
    });
    return chunkTail;
  }
  extractInput(fromPos, toPos, flags) {
    if (fromPos === void 0) {
      fromPos = 0;
    }
    if (toPos === void 0) {
      toPos = this.displayValue.length;
    }
    if (flags === void 0) {
      flags = {};
    }
    if (fromPos === toPos) return '';
    let input = '';
    this._forEachBlocksInRange(fromPos, toPos, (b, _, fromPos, toPos) => {
      input += b.extractInput(fromPos, toPos, flags);
    });
    return input;
  }
  _findStopBefore(blockIndex) {
    let stopBefore;
    for (let si = 0; si < this._stops.length; ++si) {
      const stop = this._stops[si];
      if (stop <= blockIndex) stopBefore = stop;else break;
    }
    return stopBefore;
  }

  /** Appends placeholder depending on laziness */
  _appendPlaceholder(toBlockIndex) {
    const details = new ChangeDetails();
    if (this.lazy && toBlockIndex == null) return details;
    const startBlockIter = this._mapPosToBlock(this.displayValue.length);
    if (!startBlockIter) return details;
    const startBlockIndex = startBlockIter.index;
    const endBlockIndex = toBlockIndex != null ? toBlockIndex : this._blocks.length;
    this._blocks.slice(startBlockIndex, endBlockIndex).forEach(b => {
      if (!b.lazy || toBlockIndex != null) {
        var _blocks2;
        details.aggregate(b._appendPlaceholder((_blocks2 = b._blocks) == null ? void 0 : _blocks2.length));
      }
    });
    return details;
  }

  /** Finds block in pos */
  _mapPosToBlock(pos) {
    let accVal = '';
    for (let bi = 0; bi < this._blocks.length; ++bi) {
      const block = this._blocks[bi];
      const blockStartPos = accVal.length;
      accVal += block.displayValue;
      if (pos <= accVal.length) {
        return {
          index: bi,
          offset: pos - blockStartPos
        };
      }
    }
  }
  _blockStartPos(blockIndex) {
    return this._blocks.slice(0, blockIndex).reduce((pos, b) => pos += b.displayValue.length, 0);
  }
  _forEachBlocksInRange(fromPos, toPos, fn) {
    if (toPos === void 0) {
      toPos = this.displayValue.length;
    }
    const fromBlockIter = this._mapPosToBlock(fromPos);
    if (fromBlockIter) {
      const toBlockIter = this._mapPosToBlock(toPos);
      // process first block
      const isSameBlock = toBlockIter && fromBlockIter.index === toBlockIter.index;
      const fromBlockStartPos = fromBlockIter.offset;
      const fromBlockEndPos = toBlockIter && isSameBlock ? toBlockIter.offset : this._blocks[fromBlockIter.index].displayValue.length;
      fn(this._blocks[fromBlockIter.index], fromBlockIter.index, fromBlockStartPos, fromBlockEndPos);
      if (toBlockIter && !isSameBlock) {
        // process intermediate blocks
        for (let bi = fromBlockIter.index + 1; bi < toBlockIter.index; ++bi) {
          fn(this._blocks[bi], bi, 0, this._blocks[bi].displayValue.length);
        }

        // process last block
        fn(this._blocks[toBlockIter.index], toBlockIter.index, 0, toBlockIter.offset);
      }
    }
  }
  remove(fromPos, toPos) {
    if (fromPos === void 0) {
      fromPos = 0;
    }
    if (toPos === void 0) {
      toPos = this.displayValue.length;
    }
    const removeDetails = super.remove(fromPos, toPos);
    this._forEachBlocksInRange(fromPos, toPos, (b, _, bFromPos, bToPos) => {
      removeDetails.aggregate(b.remove(bFromPos, bToPos));
    });
    return removeDetails;
  }
  nearestInputPos(cursorPos, direction) {
    if (direction === void 0) {
      direction = DIRECTION.NONE;
    }
    if (!this._blocks.length) return 0;
    const cursor = new PatternCursor(this, cursorPos);
    if (direction === DIRECTION.NONE) {
      // -------------------------------------------------
      // NONE should only go out from fixed to the right!
      // -------------------------------------------------
      if (cursor.pushRightBeforeInput()) return cursor.pos;
      cursor.popState();
      if (cursor.pushLeftBeforeInput()) return cursor.pos;
      return this.displayValue.length;
    }

    // FORCE is only about a|* otherwise is 0
    if (direction === DIRECTION.LEFT || direction === DIRECTION.FORCE_LEFT) {
      // try to break fast when *|a
      if (direction === DIRECTION.LEFT) {
        cursor.pushRightBeforeFilled();
        if (cursor.ok && cursor.pos === cursorPos) return cursorPos;
        cursor.popState();
      }

      // forward flow
      cursor.pushLeftBeforeInput();
      cursor.pushLeftBeforeRequired();
      cursor.pushLeftBeforeFilled();

      // backward flow
      if (direction === DIRECTION.LEFT) {
        cursor.pushRightBeforeInput();
        cursor.pushRightBeforeRequired();
        if (cursor.ok && cursor.pos <= cursorPos) return cursor.pos;
        cursor.popState();
        if (cursor.ok && cursor.pos <= cursorPos) return cursor.pos;
        cursor.popState();
      }
      if (cursor.ok) return cursor.pos;
      if (direction === DIRECTION.FORCE_LEFT) return 0;
      cursor.popState();
      if (cursor.ok) return cursor.pos;
      cursor.popState();
      if (cursor.ok) return cursor.pos;
      return 0;
    }
    if (direction === DIRECTION.RIGHT || direction === DIRECTION.FORCE_RIGHT) {
      // forward flow
      cursor.pushRightBeforeInput();
      cursor.pushRightBeforeRequired();
      if (cursor.pushRightBeforeFilled()) return cursor.pos;
      if (direction === DIRECTION.FORCE_RIGHT) return this.displayValue.length;

      // backward flow
      cursor.popState();
      if (cursor.ok) return cursor.pos;
      cursor.popState();
      if (cursor.ok) return cursor.pos;
      return this.nearestInputPos(cursorPos, DIRECTION.LEFT);
    }
    return cursorPos;
  }
  totalInputPositions(fromPos, toPos) {
    if (fromPos === void 0) {
      fromPos = 0;
    }
    if (toPos === void 0) {
      toPos = this.displayValue.length;
    }
    let total = 0;
    this._forEachBlocksInRange(fromPos, toPos, (b, _, bFromPos, bToPos) => {
      total += b.totalInputPositions(bFromPos, bToPos);
    });
    return total;
  }

  /** Get block by name */
  maskedBlock(name) {
    return this.maskedBlocks(name)[0];
  }

  /** Get all blocks by name */
  maskedBlocks(name) {
    const indices = this._maskedBlocks[name];
    if (!indices) return [];
    return indices.map(gi => this._blocks[gi]);
  }
  pad(flags) {
    const details = new ChangeDetails();
    this._forEachBlocksInRange(0, this.displayValue.length, b => details.aggregate(b.pad(flags)));
    return details;
  }
}
MaskedPattern.DEFAULTS = {
  ...Masked.DEFAULTS,
  lazy: true,
  placeholderChar: '_'
};
MaskedPattern.STOP_CHAR = '`';
MaskedPattern.ESCAPE_CHAR = '\\';
MaskedPattern.InputDefinition = PatternInputDefinition;
MaskedPattern.FixedDefinition = PatternFixedDefinition;
IMask.MaskedPattern = MaskedPattern;

export { MaskedPattern as default };
