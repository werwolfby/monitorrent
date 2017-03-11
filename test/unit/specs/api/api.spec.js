import fetchMock from 'fetch-mock'
import api from 'src/api/monitorrent'
import { expect } from 'chai'

describe('API', () => {
    afterEach(fetchMock.restore)

    it(`defaultClient should works`, async () => {
        const defaultClient = {
            fields: {},
            name: 'downloader',
            settings: {
                path: '/path/to/folder'
            }
        }
        fetchMock.get(`/api/default_client`, defaultClient)

        const result = await api.defaultClient()

        expect(result).to.be.eql(defaultClient)
    })

    it(`defaultClient should throw on backend errors`, async () => {
        fetchMock.get(`/api/default_client`, {status: 500, body: {title: 'ServerError', description: 'Can\'t reset status for 12 topic'}})

        const error = await expect(api.defaultClient()).to.eventually.rejectedWith(Error)

        expect(error.message).to.be.equal('ServerError')
        expect(error.description).to.be.equal('Can\'t reset status for 12 topic')
    })

    it(`defaultClient should throw on any not success response`, async () => {
        const responseError = {title: 'NotFound', description: `Page not found`}
        fetchMock.get(`/api/default_client`, {status: 404, body: responseError})

        const error = await expect(api.defaultClient()).to.eventually.rejectedWith(Error)

        expect(error.message).to.be.equal('NotFound')
        expect(error.description).to.be.equal('Page not found')
    })
})
