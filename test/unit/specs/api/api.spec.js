import fetchMock from 'fetch-mock'
import api from 'src/api/monitorrent'
import { expect } from 'chai'

describe('API', () => {
    afterEach(fetchMock.restore)

    it('getTopics should call /api/topics', async () => {
        const topics = [
            { display_name: 'Topic 1 (Season 1)', tracker: 'rutor.info', last_update: null },
            { display_name: 'Topic 2 (Season 3)', tracker: 'rutor.info', last_update: '2017-02-21T00:35:47' }
        ]
        fetchMock.get('/api/topics', topics)

        const fetchedTopics = await api.topics.all()
        expect(fetchedTopics).to.be.eql(topics)
    })

    it('getTopics should throw on /api/topics backend error', async () => {
        fetchMock.get('/api/topics', {status: 500, body: {title: 'ServerError', description: 'Can\'t get topics'}})

        const error = await expect(api.topics.all()).to.eventually.rejectedWith(Error)

        expect(error.message).to.be.equal('ServerError')
        expect(error.description).to.be.equal('Can\'t get topics')
    })

    it('getTopics should throw on /api/topics backend error', async () => {
        const responseError = {title: 'NotFound', description: `Page not found`}
        fetchMock.get('/api/topics', {status: 404, body: responseError})

        const error = await expect(api.topics.all()).to.eventually.rejectedWith(Error)

        expect(error.message).to.be.equal('NotFound')
        expect(error.description).to.be.equal('Page not found')
    })

    it(`getLogs should call /api/execute/logs?skip=0&take=10 without params`, async () => {
        const logs = {
            count: 10,
            data: []
        }
        fetchMock.get(`/api/execute/logs?skip=0&take=10`, logs)

        const fetchedLogs = await api.execute.logs()
        expect(fetchedLogs).to.be.eql(logs)
    })

    it(`getLogs should call /api/execute/logs?skip=20&take=10 only with skip=20`, async () => {
        const logs = {
            count: 10,
            data: []
        }
        fetchMock.get(`/api/execute/logs?skip=20&take=10`, logs)

        const fetchedLogs = await api.execute.logs(20)
        expect(fetchedLogs).to.be.eql(logs)
    })

    for (let [skip, take] of [[0, 1], [0, 10], [20, 10]]) {
        it(`getLogs should call /api/execute/logs?skip=${skip}&take=${take}`, async () => {
            const logs = {
                count: 10,
                data: []
            }
            fetchMock.get(`/api/execute/logs?skip=${skip}&take=${take}`, logs)

            const fetchedLogs = await api.execute.logs(skip, take)
            expect(fetchedLogs).to.be.eql(logs)
        })
    }

    for (let value of [true, false]) {
        it(`setTopicStatus(${value}) should call /api/topics/12/pause`, async () => {
            fetchMock.post(`/api/topics/12/pause`, {status: 204})
            const resp = await api.topics.setPaused(12, value)

            expect(resp.status).to.equal(204)
        })
    }

    it(`getLogs should call /api/execute/logs?skip=20&take=10 only with skip=20`, async () => {
        fetchMock.get(/\/api\/execute\/logs\?skip=\d+&take=\d+/, {status: 500, body: {title: 'ServerError', description: 'Can\'t get topics'}})

        const error = await expect(api.execute.logs(10, 20)).to.eventually.rejectedWith(Error)
        expect(error.message).to.be.equal('ServerError')
        expect(error.description).to.be.equal('Can\'t get topics')
    })

    it(`getLogs should call /api/execute/logs?skip=20&take=10 only with skip=20`, async () => {
        const responseError = {title: 'NotFound', description: `Page not found`}
        fetchMock.get(/\/api\/execute\/logs\?skip=\d+&take=\d+/, {status: 404, body: responseError})

        const error = await expect(api.execute.logs(10, 20)).to.eventually.rejectedWith(Error)

        expect(error.message).to.be.equal('NotFound')
        expect(error.description).to.be.equal('Page not found')
    })

    it(`setTopicPaused should works`, async () => {
        fetchMock.post(`/api/topics/12/pause`, {status: 204, body: ''})

        await expect(api.topics.setPaused(12, true)).to.eventually.fullfiled
    })

    it(`setTopicPaused should throw on backend errors`, async () => {
        fetchMock.post(`/api/topics/12/pause`, {status: 500, body: {title: 'ServerError', description: 'Can\'t set topic 12 pause'}})

        const err = await expect(api.topics.setPaused(12, true)).to.eventually.rejectedWith(Error)

        expect(err.message).to.be.equal('ServerError')
        expect(err.description).to.be.equal('Can\'t set topic 12 pause')
    })

    it(`setTopicPaused should throw on any not success response`, async () => {
        const responseError = {title: 'NotFound', description: `Page not found`}
        fetchMock.post(`/api/topics/12/pause`, {status: 404, body: responseError})

        const error = await expect(api.topics.setPaused(12, false)).to.eventually.rejectedWith(Error)

        expect(error.message).to.be.equal('NotFound')
        expect(error.description).to.be.equal('Page not found')
    })

    it(`resetTopicStatus should works`, async () => {
        fetchMock.post(`/api/topics/12/reset_status`, {status: 204, body: ''})

        await expect(api.topics.resetStatus(12)).to.eventually.fullfiled
    })

    it(`resetTopicStatus should throw on backend errors`, async () => {
        fetchMock.post(`/api/topics/12/reset_status`, {status: 500, body: {title: 'ServerError', description: 'Can\'t reset status for 12 topic'}})

        const err = await expect(api.topics.resetStatus(12)).to.eventually.rejectedWith(Error)

        expect(err.message).to.be.equal('ServerError')
        expect(err.description).to.be.equal('Can\'t reset status for 12 topic')
    })

    it(`resetTopicStatus should throw on any not success response`, async () => {
        const responseError = {title: 'NotFound', description: `Page not found`}
        fetchMock.post(`/api/topics/12/reset_status`, {status: 404, body: responseError})

        const error = await expect(api.topics.resetStatus(12)).to.eventually.rejectedWith(Error)

        expect(error.message).to.be.equal('NotFound')
        expect(error.description).to.be.equal('Page not found')
    })

    it(`deleteTopic should works`, async () => {
        fetchMock.delete(`/api/topics/12`, {status: 204, body: ''})

        await expect(api.topics.delete(12)).to.eventually.fullfiled
    })

    it(`deleteTopic should throw on backend errors`, async () => {
        fetchMock.delete(`/api/topics/12`, {status: 500, body: {title: 'ServerError', description: 'Can\'t reset status for 12 topic'}})

        const error = await expect(api.topics.delete(12)).to.eventually.rejectedWith(Error)

        expect(error.message).to.be.equal('ServerError')
        expect(error.description).to.be.equal('Can\'t reset status for 12 topic')
    })

    it(`deleteTopic should throw on any not success response`, async () => {
        const responseError = {title: 'NotFound', description: `Page not found`}
        fetchMock.delete(`/api/topics/12`, {status: 404, body: responseError})

        const error = await expect(api.topics.delete(12)).to.eventually.rejectedWith(Error)

        expect(error.message).to.be.equal('NotFound')
        expect(error.description).to.be.equal('Page not found')
    })

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

    it(`parseUrl should works and encode url`, async () => {
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

    it(`parseUrl should throw on backend errors`, async () => {
        const responseError = {title: 'ServerError', description: 'Can\'t reset status for 12 topic'}
        fetchMock.get(`/api/topics/parse?url=https%3A%2F%2Fwww.lostfilm.tv%2Fseries%2FTaboo%2F`, {status: 500, body: responseError})

        const error = await expect(api.topics.parseUrl('https://www.lostfilm.tv/series/Taboo/')).to.eventually.rejectedWith(Error)

        expect(error.message).to.be.equal('ServerError')
        expect(error.description).to.be.equal('Can\'t reset status for 12 topic')
    })

    it(`parseUrl should throw cant parse error`, async () => {
        const responseError = {title: 'CantParse', description: 'Can\'t parse url: \'https://www.lostfilm.tv/series/\''}
        fetchMock.get(`/api/topics/parse?url=https%3A%2F%2Fwww.lostfilm.tv%2Fseries%2F`, {status: 400, body: responseError})

        const error = await expect(api.topics.parseUrl('https://www.lostfilm.tv/series/')).to.eventually.rejectedWith(Error)

        expect(error.message).to.be.equal('CantParse')
        expect(error.description).to.be.equal('Can\'t parse url: \'https://www.lostfilm.tv/series/\'')
    })

    it(`parseUrl should throw on any not success response`, async () => {
        const responseError = {title: 'NotFound', description: `Page not found`}
        fetchMock.get(`/api/topics/parse?url=https%3A%2F%2Fwww.lostfilm.tv%2Fseries%2FTaboo%2F`, {status: 404, body: responseError})

        const error = await expect(api.topics.parseUrl('https://www.lostfilm.tv/series/Taboo/')).to.eventually.rejectedWith(Error)

        expect(error.message).to.be.equal('NotFound')
        expect(error.description).to.be.equal('Page not found')
    })

    it(`addTopic should works`, async () => {
        fetchMock.post(`/api/topics`, {status: 201, headers: {Location: '/api/topics/12'}})

        const settings = {display_name: 'Taboo', quality: '720p'}
        const result = await api.topics.add('https://www.lostfilm.tv/series/Taboo/', settings)

        expect(result).to.be.equal(12)
    })

    it(`addTopic should throw on backend errors`, async () => {
        const responseError = {title: 'WrongParameters', description: `Can't add topic`}
        fetchMock.post(`/api/topics`, {status: 400, body: responseError})

        const settings = {display_name: 'Taboo', quality: '720p'}
        const error = await expect(api.topics.add('https://www.lostfilm.tv/series/Taboo/', settings)).to.eventually.rejectedWith(Error)

        expect(error.message).to.be.equal('WrongParameters')
        expect(error.description).to.be.equal(`Can't add topic`)
    })

    it(`addTopic should throw on backend errors`, async () => {
        const responseError = {title: 'ServerError', description: `Can't add topic`}
        fetchMock.post(`/api/topics`, {status: 500, body: responseError})

        const settings = {display_name: 'Taboo', quality: '720p'}
        const error = await expect(api.topics.add('https://www.lostfilm.tv/series/Taboo/', settings)).to.eventually.rejectedWith(Error)

        expect(error.message).to.be.equal('ServerError')
        expect(error.description).to.be.equal(`Can't add topic`)
    })

    it(`getTopic should works`, async () => {
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

    it(`getTopic should works`, async () => {
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

    it(`getTopic should throw on backend errors`, async () => {
        const responseError = {title: 'NotFound', description: `Can't find topic: 12`}
        fetchMock.get(`/api/topics/12`, {status: 404, body: responseError})

        const error = await expect(api.topics.get(12)).to.eventually.rejectedWith(Error)

        expect(error.message).to.be.equal('NotFound')
        expect(error.description).to.be.equal(`Can't find topic: 12`)
    })

    it(`editTopic should works`, async () => {
        fetchMock.put(`/api/topics/12`, {status: 204})

        const settings = {display_name: 'Edited', id: 12}
        await api.topics.edit(12, settings)
    })
})
