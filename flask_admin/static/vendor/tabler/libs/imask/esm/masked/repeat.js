import ChangeDetails from '../core/change-details.js';
import IMask from '../core/holder.js';
import createMask, { normalizeOpts } from './factory.js';
import MaskedPattern from './pattern.js';
import '../core/utils.js';
import './base.js';
import '../core/continuous-tail-details.js';
import './pattern/chunk-tail-details.js';
import './pattern/cursor.js';
import './pattern/fixed-definition.js';
import './pattern/input-definition.js';
import './regexp.js';

/** Pattern mask */
class RepeatBlock extends MaskedPattern {
  get repeatFrom() {
    var _ref;
    return (_ref = Array.isArray(this.repeat) ? this.repeat[0] : this.repeat === Infinity ? 0 : this.repeat) != null ? _ref : 0;
  }
  get repeatTo() {
    var _ref2;
    return (_ref2 = Array.isArray(this.repeat) ? this.repeat[1] : this.repeat) != null ? _ref2 : Infinity;
  }
  constructor(opts) {
    super(opts);
  }
  updateOptions(opts) {
    super.updateOptions(opts);
  }
  _update(opts) {
    var _ref3, _ref4, _this$_blocks;
    const {
      repeat,
      ...blockOpts
    } = normalizeOpts(opts); // TODO type
    this._blockOpts = Object.assign({}, this._blockOpts, blockOpts);
    const block = createMask(this._blockOpts);
    this.repeat = (_ref3 = (_ref4 = repeat != null ? repeat : block.repeat) != null ? _ref4 : this.repeat) != null ? _ref3 : Infinity; // TODO type

    super._update({
      mask: 'm'.repeat(Math.max(this.repeatTo === Infinity && ((_this$_blocks = this._blocks) == null ? void 0 : _this$_blocks.length) || 0, this.repeatFrom)),
      blocks: {
        m: block
      },
      eager: block.eager,
      overwrite: block.overwrite,
      skipInvalid: block.skipInvalid,
      lazy: block.lazy,
      placeholderChar: block.placeholderChar,
      displayChar: block.displayChar
    });
  }
  _allocateBlock(bi) {
    if (bi < this._blocks.length) return this._blocks[bi];
    if (this.repeatTo === Infinity || this._blocks.length < this.repeatTo) {
      this._blocks.push(createMask(this._blockOpts));
      this.mask += 'm';
      return this._blocks[this._blocks.length - 1];
    }
  }
  _appendCharRaw(ch, flags) {
    if (flags === void 0) {
      flags = {};
    }
    const details = new ChangeDetails();
    for (let bi = (_this$_mapPosToBlock$ = (_this$_mapPosToBlock = this._mapPosToBlock(this.displayValue.length)) == null ? void 0 : _this$_mapPosToBlock.index) != null ? _this$_mapPosToBlock$ : Math.max(this._blocks.length - 1, 0), block, allocated;
    // try to get a block or
    // try to allocate a new block if not allocated already
    block = (_this$_blocks$bi = this._blocks[bi]) != null ? _this$_blocks$bi : allocated = !allocated && this._allocateBlock(bi); ++bi) {
      var _this$_mapPosToBlock$, _this$_mapPosToBlock, _this$_blocks$bi, _flags$_beforeTailSta;
      const blockDetails = block._appendChar(ch, {
        ...flags,
        _beforeTailState: (_flags$_beforeTailSta = flags._beforeTailState) == null || (_flags$_beforeTailSta = _flags$_beforeTailSta._blocks) == null ? void 0 : _flags$_beforeTailSta[bi]
      });
      if (blockDetails.skip && allocated) {
        // remove the last allocated block and break
        this._blocks.pop();
        this.mask = this.mask.slice(1);
        break;
      }
      details.aggregate(blockDetails);
      if (blockDetails.consumed) break; // go next char
    }
    return details;
  }
  _trimEmptyTail(fromPos, toPos) {
    var _this$_mapPosToBlock2, _this$_mapPosToBlock3;
    if (fromPos === void 0) {
      fromPos = 0;
    }
    const firstBlockIndex = Math.max(((_this$_mapPosToBlock2 = this._mapPosToBlock(fromPos)) == null ? void 0 : _this$_mapPosToBlock2.index) || 0, this.repeatFrom, 0);
    let lastBlockIndex;
    if (toPos != null) lastBlockIndex = (_this$_mapPosToBlock3 = this._mapPosToBlock(toPos)) == null ? void 0 : _this$_mapPosToBlock3.index;
    if (lastBlockIndex == null) lastBlockIndex = this._blocks.length - 1;
    let removeCount = 0;
    for (let blockIndex = lastBlockIndex; firstBlockIndex <= blockIndex; --blockIndex, ++removeCount) {
      if (this._blocks[blockIndex].unmaskedValue) break;
    }
    if (removeCount) {
      this._blocks.splice(lastBlockIndex - removeCount + 1, removeCount);
      this.mask = this.mask.slice(removeCount);
    }
  }
  reset() {
    super.reset();
    this._trimEmptyTail();
  }
  remove(fromPos, toPos) {
    if (fromPos === void 0) {
      fromPos = 0;
    }
    if (toPos === void 0) {
      toPos = this.displayValue.length;
    }
    const removeDetails = super.remove(fromPos, toPos);
    this._trimEmptyTail(fromPos, toPos);
    return removeDetails;
  }
  totalInputPositions(fromPos, toPos) {
    if (fromPos === void 0) {
      fromPos = 0;
    }
    if (toPos == null && this.repeatTo === Infinity) return Infinity;
    return super.totalInputPositions(fromPos, toPos);
  }
  get state() {
    return super.state;
  }
  set state(state) {
    this._blocks.length = state._blocks.length;
    this.mask = this.mask.slice(0, this._blocks.length);
    super.state = state;
  }
}
IMask.RepeatBlock = RepeatBlock;

export { RepeatBlock as default };
