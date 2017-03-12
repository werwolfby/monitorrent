import fetchMock from 'fetch-mock'
import api from 'src/api/monitorrent'
import { expect } from 'chai'

describe('API.execute', () => {
    afterEach(fetchMock.restore)

    describe(`logs`, function () {
        it(`'logs' should call /api/execute/logs?skip=0&take=10 without params`, async () => {
            const logs = {
                count: 10,
                data: []
            }
            fetchMock.get(`/api/execute/logs?skip=0&take=10`, logs)

            const fetchedLogs = await api.execute.logs()
            expect(fetchedLogs).to.be.eql(logs)
        })

        it(`'logs' should call /api/execute/logs?skip=20&take=10 only with skip=20`, async () => {
            const logs = {
                count: 10,
                data: []
            }
            fetchMock.get(`/api/execute/logs?skip=20&take=10`, logs)

            const fetchedLogs = await api.execute.logs(20)
            expect(fetchedLogs).to.be.eql(logs)
        })

        for (let [skip, take] of [[0, 1], [0, 10], [20, 10]]) {
            it(`'logs' should call /api/execute/logs?skip=${skip}&take=${take}`, async () => {
                const logs = {
                    count: 10,
                    data: []
                }
                fetchMock.get(`/api/execute/logs?skip=${skip}&take=${take}`, logs)

                const fetchedLogs = await api.execute.logs(skip, take)
                expect(fetchedLogs).to.be.eql(logs)
            })
        }

        it(`'logs' should call /api/execute/logs?skip=20&take=10 only with skip=20`, async () => {
            fetchMock.get(/\/api\/execute\/logs\?skip=\d+&take=\d+/, {status: 500, body: {title: 'ServerError', description: 'Can\'t get topics'}})

            const error = await expect(api.execute.logs(10, 20)).to.eventually.rejectedWith(Error)
            expect(error.message).to.be.equal('ServerError')
            expect(error.description).to.be.equal('Can\'t get topics')
        })

        it(`'logs' should throw error on backend error`, async () => {
            const responseError = {title: 'NotFound', description: `Page not found`}
            fetchMock.get(/\/api\/execute\/logs\?skip=\d+&take=\d+/, {status: 404, body: responseError})

            const error = await expect(api.execute.logs(10, 20)).to.eventually.rejectedWith(Error)

            expect(error.message).to.be.equal('NotFound')
            expect(error.description).to.be.equal('Page not found')
        })
    })

    describe(`current`, function () {
        it(`'current' should call /api/execute/logs/current`, async () => {
            const current = {
                is_running: false,
                logs: []
            }
            fetchMock.get(`/api/execute/logs/current`, current)

            const fetchedLogs = await api.execute.current()
            expect(fetchedLogs).to.be.eql(current)
        })

        it(`'current' should throw NotFound error on 404 error`, async () => {
            const responseError = {title: 'NotFound', description: `Page not found`}
            fetchMock.get(`/api/execute/logs/current`, {status: 404, body: responseError})

            const error = await expect(api.execute.current()).to.eventually.rejectedWith(Error)

            expect(error.message).to.be.equal('NotFound')
            expect(error.description).to.be.equal('Page not found')
        })

        it(`'current' should throw InternalError error on 500 error`, async () => {
            const responseError = {title: 'InternalError', description: `Internal Error`}
            fetchMock.get(`/api/execute/logs/current`, {status: 500, body: responseError})

            const error = await expect(api.execute.current()).to.eventually.rejectedWith(Error)

            expect(error.message).to.be.equal('InternalError')
            expect(error.description).to.be.equal('Internal Error')
        })
    })

    describe(`details`, function () {
        it(`'details' should call /api/execute/logs/123/details`, async () => {
            const details = {
                is_running: false,
                logs: []
            }
            fetchMock.get(`/api/execute/logs/123/details`, details)

            const fetchedLogs = await api.execute.details(123)
            expect(fetchedLogs).to.be.eql(details)
        })

        it(`'details' should call /api/execute/logs/123/details?after=456`, async () => {
            const details = {
                is_running: false,
                logs: []
            }
            fetchMock.get(`/api/execute/logs/123/details?after=456`, details)

            const fetchedLogs = await api.execute.details(123, 456)
            expect(fetchedLogs).to.be.eql(details)
        })

        it(`'details' should throw NotFound error on 404 error`, async () => {
            const responseError = {title: 'NotFound', description: `Page not found`}
            fetchMock.get(`/api/execute/logs/123/details`, {status: 404, body: responseError})

            const error = await expect(api.execute.details(123)).to.eventually.rejectedWith(Error)

            expect(error.message).to.be.equal('NotFound')
            expect(error.description).to.be.equal('Page not found')
        })

        it(`'details' should throw InternalError error on 500 error`, async () => {
            const responseError = {title: 'InternalError', description: `Internal Error`}
            fetchMock.get(`/api/execute/logs/123/details`, {status: 500, body: responseError})

            const error = await expect(api.execute.details(123)).to.eventually.rejectedWith(Error)

            expect(error.message).to.be.equal('InternalError')
            expect(error.description).to.be.equal('Internal Error')
        })
    })

    describe(`execute`, function () {
        it(`'execute' should call /api/execute/call without params`, async () => {
            fetchMock.post(`/api/execute/call`, {body: ''})

            const result = await api.execute.execute()
            expect(result).to.be.true
        })

        it(`'execute' should call /api/execute/call?ids=1,2,3 with params`, async () => {
            fetchMock.post(`/api/execute/call?ids=1,2,3`, {body: ''})

            const result = await api.execute.execute([1, 2, 3])
            expect(result).to.be.true
        })

        it(`'execute' throw exception on error`, async () => {
            fetchMock.post(`/api/execute/call`, {status: 500, body: {title: 'ServerError', description: 'Can\'t execute'}})

            const error = await expect(api.execute.execute()).to.eventually.rejectedWith(Error)

            expect(error.message).to.be.equal('ServerError')
            expect(error.description).to.be.equal('Can\'t execute')
        })
    })

    describe(`executeTracker`, function () {
        it(`'executeTracker' should call /api/execute/call?tracker=lostfilm.tv without params`, async () => {
            fetchMock.post(`/api/execute/call?tracker=lostfilm.tv`, {body: ''})

            const result = await api.execute.executeTracker('lostfilm.tv')
            expect(result).to.be.true
        })

        it(`'executeTracker' throw exception on error`, async () => {
            fetchMock.post(`/api/execute/call?tracker=lostfilm.tv`, {status: 500, body: {title: 'ServerError', description: 'Can\'t execute'}})

            const error = await expect(api.execute.executeTracker('lostfilm.tv')).to.eventually.rejectedWith(Error)

            expect(error.message).to.be.equal('ServerError')
            expect(error.description).to.be.equal('Can\'t execute')
        })
    })
})
