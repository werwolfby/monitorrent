import fetchMock from 'fetch-mock'
import api from 'src/api/monitorrent'
import { expect } from 'chai'

describe('API.topics', () => {
    afterEach(fetchMock.restore)

    describe(`get`, function () {
        it(`'get' should call /api/topics`, async () => {
            const topics = [
                { display_name: 'Topic 1 (Season 1)', tracker: 'rutor.info', last_update: null },
                { display_name: 'Topic 2 (Season 3)', tracker: 'rutor.info', last_update: '2017-02-21T00:35:47' }
            ]
            fetchMock.get('/api/topics', topics)

            const fetchedTopics = await api.topics.all()
            expect(fetchedTopics).to.be.eql(topics)
        })

        it(`'get' should throw on /api/topics backend error`, async () => {
            fetchMock.get('/api/topics', {status: 500, body: {title: 'ServerError', description: 'Can\'t get topics'}})

            const error = await expect(api.topics.all()).to.eventually.rejectedWith(Error)

            expect(error.message).to.be.equal('ServerError')
            expect(error.description).to.be.equal('Can\'t get topics')
        })

        it(`'get' should throw on /api/topics backend error`, async () => {
            const responseError = {title: 'NotFound', description: `Page not found`}
            fetchMock.get('/api/topics', {status: 404, body: responseError})

            const error = await expect(api.topics.all()).to.eventually.rejectedWith(Error)

            expect(error.message).to.be.equal('NotFound')
            expect(error.description).to.be.equal('Page not found')
        })
    })

    describe(`setPaused`, function () {
        for (let value of [true, false]) {
            it(`'setPaused(${value})' should works`, async () => {
                fetchMock.post(`/api/topics/12/pause`, {status: 204})
                const resp = await api.topics.setPaused(12, value)

                expect(resp.status).to.equal(204)
            })
        }

        it(`'setPaused' should throw on backend errors`, async () => {
            fetchMock.post(`/api/topics/12/pause`, {status: 500, body: {title: 'ServerError', description: 'Can\'t set topic 12 pause'}})

            const err = await expect(api.topics.setPaused(12, true)).to.eventually.rejectedWith(Error)

            expect(err.message).to.be.equal('ServerError')
            expect(err.description).to.be.equal('Can\'t set topic 12 pause')
        })

        it(`'setPaused' should throw on any not success response`, async () => {
            const responseError = {title: 'NotFound', description: `Page not found`}
            fetchMock.post(`/api/topics/12/pause`, {status: 404, body: responseError})

            const error = await expect(api.topics.setPaused(12, false)).to.eventually.rejectedWith(Error)

            expect(error.message).to.be.equal('NotFound')
            expect(error.description).to.be.equal('Page not found')
        })
    })

    describe(`resetStatus`, function () {
        it(`'resetStatus' should works`, async () => {
            fetchMock.post(`/api/topics/12/reset_status`, {status: 204, body: ''})

            await expect(api.topics.resetStatus(12)).to.eventually.fullfiled
        })

        it(`'resetStatus' should throw on backend errors`, async () => {
            fetchMock.post(`/api/topics/12/reset_status`, {status: 500, body: {title: 'ServerError', description: 'Can\'t reset status for 12 topic'}})

            const err = await expect(api.topics.resetStatus(12)).to.eventually.rejectedWith(Error)

            expect(err.message).to.be.equal('ServerError')
            expect(err.description).to.be.equal('Can\'t reset status for 12 topic')
        })

        it(`'resetStatus' should throw on any not success response`, async () => {
            const responseError = {title: 'NotFound', description: `Page not found`}
            fetchMock.post(`/api/topics/12/reset_status`, {status: 404, body: responseError})

            const error = await expect(api.topics.resetStatus(12)).to.eventually.rejectedWith(Error)

            expect(error.message).to.be.equal('NotFound')
            expect(error.description).to.be.equal('Page not found')
        })
    })

    describe(`delete`, function () {
        it(`'delete' should works`, async () => {
            fetchMock.delete(`/api/topics/12`, {status: 204, body: ''})

            await expect(api.topics.delete(12)).to.eventually.fullfiled
        })

        it(`'delete' should throw on backend errors`, async () => {
            fetchMock.delete(`/api/topics/12`, {status: 500, body: {title: 'ServerError', description: 'Can\'t reset status for 12 topic'}})

            const error = await expect(api.topics.delete(12)).to.eventually.rejectedWith(Error)

            expect(error.message).to.be.equal('ServerError')
            expect(error.description).to.be.equal('Can\'t reset status for 12 topic')
        })

        it(`'delete' should throw on any not success response`, async () => {
            const responseError = {title: 'NotFound', description: `Page not found`}
            fetchMock.delete(`/api/topics/12`, {status: 404, body: responseError})

            const error = await expect(api.topics.delete(12)).to.eventually.rejectedWith(Error)

            expect(error.message).to.be.equal('NotFound')
            expect(error.description).to.be.equal('Page not found')
        })
    })

    describe(`parseUrl`, function () {
        it(`'parseUrl' should works and encode url`, async () => {
            const parseResult = {
                settings: {
                    display_name: 'Табу / Taboo',
                    quality: '720p'
                },
                form: [
                    {
                        type: 'row',
                        content: [
                            {
                                type: 'text',
                                label: 'Name',
                                flex: 70,
                                model: 'display_name'
                            },
                            {
                                options: ['SD', '720p', '1080p'],
                                type: 'select',
                                label: 'Quality',
                                flex: 30,
                                model: 'quality'
                            }
                        ]
                    }
                ]
            }
            fetchMock.get(`/api/topics/parse?url=https%3A%2F%2Fwww.lostfilm.tv%2Fseries%2FTaboo%2F`, parseResult)

            const result = await api.topics.parseUrl('https://www.lostfilm.tv/series/Taboo/')

            expect(result).to.be.eql(parseResult)
        })

        it(`'parseUrl' should throw on backend errors`, async () => {
            const responseError = {title: 'ServerError', description: 'Can\'t reset status for 12 topic'}
            fetchMock.get(`/api/topics/parse?url=https%3A%2F%2Fwww.lostfilm.tv%2Fseries%2FTaboo%2F`, {status: 500, body: responseError})

            const error = await expect(api.topics.parseUrl('https://www.lostfilm.tv/series/Taboo/')).to.eventually.rejectedWith(Error)

            expect(error.message).to.be.equal('ServerError')
            expect(error.description).to.be.equal('Can\'t reset status for 12 topic')
        })

        it(`'parseUrl' should throw can't parse error`, async () => {
            const responseError = {title: 'CantParse', description: 'Can\'t parse url: \'https://www.lostfilm.tv/series/\''}
            fetchMock.get(`/api/topics/parse?url=https%3A%2F%2Fwww.lostfilm.tv%2Fseries%2F`, {status: 400, body: responseError})

            const error = await expect(api.topics.parseUrl('https://www.lostfilm.tv/series/')).to.eventually.rejectedWith(Error)

            expect(error.message).to.be.equal('CantParse')
            expect(error.description).to.be.equal('Can\'t parse url: \'https://www.lostfilm.tv/series/\'')
        })

        it(`'parseUrl' should throw on any not success response`, async () => {
            const responseError = {title: 'NotFound', description: `Page not found`}
            fetchMock.get(`/api/topics/parse?url=https%3A%2F%2Fwww.lostfilm.tv%2Fseries%2FTaboo%2F`, {status: 404, body: responseError})

            const error = await expect(api.topics.parseUrl('https://www.lostfilm.tv/series/Taboo/')).to.eventually.rejectedWith(Error)

            expect(error.message).to.be.equal('NotFound')
            expect(error.description).to.be.equal('Page not found')
        })
    })

    describe(`add`, function () {
        it(`'add' should works`, async () => {
            fetchMock.post(`/api/topics`, {status: 201, headers: {Location: '/api/topics/12'}})

            const settings = {display_name: 'Taboo', quality: '720p'}
            const result = await api.topics.add('https://www.lostfilm.tv/series/Taboo/', settings)

            expect(result).to.be.equal(12)
        })

        it(`'add' should throw on backend errors`, async () => {
            const responseError = {title: 'WrongParameters', description: `Can't add topic`}
            fetchMock.post(`/api/topics`, {status: 400, body: responseError})

            const settings = {display_name: 'Taboo', quality: '720p'}
            const error = await expect(api.topics.add('https://www.lostfilm.tv/series/Taboo/', settings)).to.eventually.rejectedWith(Error)

            expect(error.message).to.be.equal('WrongParameters')
            expect(error.description).to.be.equal(`Can't add topic`)
        })

        it(`'add' should throw on backend errors`, async () => {
            const responseError = {title: 'ServerError', description: `Can't add topic`}
            fetchMock.post(`/api/topics`, {status: 500, body: responseError})

            const settings = {display_name: 'Taboo', quality: '720p'}
            const error = await expect(api.topics.add('https://www.lostfilm.tv/series/Taboo/', settings)).to.eventually.rejectedWith(Error)

            expect(error.message).to.be.equal('ServerError')
            expect(error.description).to.be.equal(`Can't add topic`)
        })
    })

    describe(`get`, function () {
        it(`'get' should works`, async () => {
            const topicResult = {
                settings: {
                    last_update: '2016-12-27T20:30:11.744680+00:00',
                    download_dir: null,
                    display_name: 'Табу / Taboo',
                    info: null,
                    id: 12,
                    status: 'Ok',
                    url: 'http://rutor.is/torrent/498004'
                },
                form: [
                    {
                        type: 'row',
                        content: [
                            {
                                type: 'text',
                                label: 'Name',
                                flex: 100,
                                model: 'display_name'
                            }
                        ]
                    }
                ]
            }

            fetchMock.get(`/api/topics/12`, topicResult)

            const result = await api.topics.get(12)

            expect(result).to.be.eql(topicResult)
        })

        it(`'get' should works`, async () => {
            const topicResult = {
                settings: {
                    last_update: '2016-12-27T20:30:11.744680+00:00',
                    download_dir: null,
                    display_name: 'Табу / Taboo',
                    info: null,
                    id: 12,
                    status: 'Ok',
                    url: 'http://rutor.is/torrent/498004'
                },
                form: [
                    {
                        type: 'row',
                        content: [
                            {
                                type: 'text',
                                label: 'Name',
                                flex: 100,
                                model: 'display_name'
                            }
                        ]
                    }
                ]
            }

            fetchMock.get(`/api/topics/12`, topicResult)

            const result = await api.topics.get(12)

            expect(result).to.be.eql(topicResult)
        })

        it(`'get' should throw on backend errors`, async () => {
            const responseError = {title: 'NotFound', description: `Can't find topic: 12`}
            fetchMock.get(`/api/topics/12`, {status: 404, body: responseError})

            const error = await expect(api.topics.get(12)).to.eventually.rejectedWith(Error)

            expect(error.message).to.be.equal('NotFound')
            expect(error.description).to.be.equal(`Can't find topic: 12`)
        })
    })

    describe(`edit`, function () {
        it(`'edit' should works`, async () => {
            fetchMock.put(`/api/topics/12`, {status: 204})

            const settings = {display_name: 'Edited', id: 12}
            await api.topics.edit(12, settings)
        })
    })
})
