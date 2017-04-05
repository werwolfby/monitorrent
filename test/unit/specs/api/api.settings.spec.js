import fetchMock from 'fetch-mock'
import api from 'src/api/monitorrent'
import { expect } from 'chai'

describe('API.settings', () => {
    afterEach(fetchMock.restore)

    describe(`updateInterval`, function () {
        it(`'updateInterval' should call /api/settings/execute`, async () => {
            const result = {
                interval: 3600,
                last_execute: '2017-03-30T11:52:50.126100+00:00'
            }
            fetchMock.get(`/api/settings/execute`, result)

            const interval = await api.settings.getUpdateInterval()
            expect(interval).to.be.eql(60)
        })

        it(`'updateInterval' should update interval on backend`, async () => {
            const mock = fetchMock.put(`/api/settings/execute`, {status: 204})

            await api.settings.setUpdateInterval(60)

            expect(mock.called())
            expect(JSON.parse(mock.lastCall()[1].body)).to.be.eql({interval: 3600})
        })

        it(`'updateInterval' should throw NotFound error on 404 error`, async () => {
            const responseError = {title: 'NotFound', description: `Page not found`}
            fetchMock.get(`/api/settings/execute`, {status: 404, body: responseError})

            const error = await expect(api.settings.getUpdateInterval()).to.eventually.rejectedWith(Error)

            expect(error.message).to.be.equal('NotFound')
            expect(error.description).to.be.equal('Page not found')
        })
    })

    describe(`proxy`, function () {
        describe(`enabled`, function () {
            it(`'isEnabled' should call /api/settings/proxy/enabled`, async () => {
                const result = {
                    enabled: true
                }
                fetchMock.get(`/api/settings/proxy/enabled`, result)

                const interval = await api.settings.proxy.isEnabled()
                expect(interval).to.be.true
            })

            it(`'isEnabled' should update enabled on backend`, async () => {
                const mock = fetchMock.put(`/api/settings/proxy/enabled`, {status: 204})

                await api.settings.proxy.setEnabled(false)

                expect(mock.called())
                expect(JSON.parse(mock.lastCall()[1].body)).to.be.eql({enabled: false})
            })

            it(`'isEnabled' should throw NotFound error on 404 error`, async () => {
                const responseError = {title: 'NotFound', description: `Page not found`}
                fetchMock.get(`/api/settings/proxy/enabled`, {status: 404, body: responseError})

                const error = await expect(api.settings.proxy.isEnabled()).to.eventually.rejectedWith(Error)

                expect(error.message).to.be.equal('NotFound')
                expect(error.description).to.be.equal('Page not found')
            })
        })

        describe(`url`, function () {
            const urls = [
                {key: 'http', value: 'http://localhost:8888'},
                {key: 'https', value: 'https://localhost:8888'}
            ]

            urls.forEach(function ({key, value}) {
                it(`'getUrl(${key})' should call /api/settings/proxy?key=${key}`, async () => {
                    const result = {
                        url: value
                    }
                    fetchMock.get(`/api/settings/proxy?key=${key}`, result)

                    const url = await api.settings.proxy.getUrl(key)
                    expect(url).to.be.equal(value)
                })
            })

            it(`'setUrl' should update enabled on backend`, async () => {
                const mock = fetchMock.put(`/api/settings/proxy?key=http`, {status: 204})

                await api.settings.proxy.setUrl('http', 'http://localhost:8888')

                expect(mock.called())
                expect(JSON.parse(mock.lastCall()[1].body)).to.be.eql({url: 'http://localhost:8888'})
            })

            it(`'getUrl' should return null on 404 error`, async () => {
                const responseError = {title: 'NotFound', description: `Page not found`}
                fetchMock.get(`/api/settings/proxy?key=http`, {status: 404, body: responseError})

                const url = await api.settings.proxy.getUrl('http')
                expect(url).to.be.null
            })
        })
    })

    describe(`newVersionChecker`, function () {
        it(`'newVersionChecker' should call /api/settings/new-version-checker`, async () => {
            const result = {
                enabled: false,
                include_prerelease: true,
                interval: 7200
            }
            fetchMock.get(`/api/settings/new-version-checker`, result)

            const response = await api.settings.getNewVersionChecker()
            expect(response).to.be.eql({...result, interval: 7200 / 60})
        })

        const patches = [
            {key: 'enabled', value: true},
            {key: 'include_prerelease', value: false},
            {key: 'interval', value: 60, eql: 3600}
        ]

        patches.forEach(function ({key, value, eql}) {
            it(`'updateNewVersionChecker({${key}: ${value}})' should update value on backend`, async () => {
                const mock = fetchMock.patch(`/api/settings/new-version-checker`, {status: 204})

                await api.settings.updateNewVersionChecker({[key]: value})

                expect(mock.called())
                expect(JSON.parse(mock.lastCall()[1].body)).to.be.eql({[key]: eql || value})
            })
        })

        it(`'updateNewVersionChecker' should update value on backend`, async () => {
            const mock = fetchMock.patch(`/api/settings/new-version-checker`, {status: 204})

            await api.settings.updateNewVersionChecker({enabled: false, include_prerelease: true, interval: 60})

            expect(mock.called())
            expect(JSON.parse(mock.lastCall()[1].body)).to.be.eql({enabled: false, include_prerelease: true, interval: 3600})
        })

        it(`'newVersionChecker' should throw NotFound error on 404 error`, async () => {
            const responseError = {title: 'NotFound', description: `Page not found`}
            fetchMock.get(`/api/settings/new-version-checker`, {status: 404, body: responseError})

            const error = await expect(api.settings.getNewVersionChecker()).to.eventually.rejectedWith(Error)

            expect(error.message).to.be.equal('NotFound')
            expect(error.description).to.be.equal('Page not found')
        })
    })
})
