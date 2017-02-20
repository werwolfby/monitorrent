import { formatDate, isNull } from 'src/filters'

describe('filters test', () => {
    it('formatDate should format value with default format', () => {
        expect(formatDate(new Date(2017, 1, 21, 0, 20, 35))).to.be.equal('21.02.2017 00:20:35')
    })

    it('formatDate should format value with provided format', () => {
        expect(formatDate(new Date(2017, 1, 21, 0, 20, 35), 'YYYY-MM-DD HH-mm-ss')).to.be.equal('2017-02-21 00-20-35')
    })

    it('isNull should return value', () => {
        expect(isNull('value', 'nullValue')).to.be.equal('value')
    })

    for (var value of [null, undefined]) {
        it(`isNull should return null value for ${value}`, () => {
            expect(isNull(value, 'nullValue')).to.be.equal('nullValue')
        })
    }
})
