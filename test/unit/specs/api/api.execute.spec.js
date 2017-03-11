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
})
