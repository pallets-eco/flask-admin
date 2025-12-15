export type ChangeDetailsOptions = Pick<ChangeDetails, 'inserted' | 'tailShift' | 'rawInserted' | 'skip'>;
/** Provides details of changing model value */
export default class ChangeDetails {
    /** Inserted symbols */
    inserted: string;
    /** Additional offset if any changes occurred before tail */
    tailShift: number;
    /** Raw inserted is used by dynamic mask */
    rawInserted: string;
    /** Can skip chars */
    skip: boolean;
    static normalize(prep: string | [string, ChangeDetails]): [string, ChangeDetails];
    constructor(details?: Partial<ChangeDetailsOptions>);
    /** Aggregate changes */
    aggregate(details: ChangeDetails): this;
    /** Total offset considering all changes */
    get offset(): number;
    get consumed(): boolean;
    equals(details: ChangeDetails): boolean;
}
//# sourceMappingURL=change-details.d.ts.map