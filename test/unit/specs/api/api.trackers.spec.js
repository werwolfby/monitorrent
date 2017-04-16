import fetchMock from 'fetch-mock'
import api from 'src/api/monitorrent'
import { expect } from 'chai'

describe('API.trackers', function () {
    afterEach(fetchMock.restore)

    describe('all', function () {
        it(`'all' should call /api/trackers`, async () => {
            const result = [
                {
                    'name': 'tracker1.org',
                    'form': [
                        {
                            'content': [
                                {'model': 'username', 'type': 'text', 'label': 'Username', 'flex': 50},
                                {'model': 'password', 'type': 'password', 'label': 'Password', 'flex': 50}
                            ],
                            'type': 'row'
                        }
                    ]
                },
                {'name': 'tracker2.com', 'form': null}
            ]

            fetchMock.get(`/api/trackers`, result)

            const trackers = await api.trackers.all()

            expect(trackers).to.be.eql(result)
        })

        it(`'all' should throw NotFound error on 404 error`, async () => {
            const responseError = {title: 'NotFound', description: `Page not found`}
            fetchMock.get(`/api/trackers`, {status: 404, body: responseError})

            const error = await expect(api.trackers.all()).to.eventually.rejectedWith(Error)

            expect(error.message).to.be.equal('NotFound')
            expect(error.description).to.be.equal('Page not found')
        })

        it(`'all' should throw Error error on 500 error`, async () => {
            const responseError = {title: 'Error'}
            fetchMock.get(`/api/trackers`, {status: 500, body: responseError})

            const error = await expect(api.trackers.all()).to.eventually.rejectedWith(Error)

            expect(error.message).to.be.equal('Error')
        })
    })

    describe('tracker', function () {
        it(`'tracker' should call /api/trackers`, async () => {
            const result = {can_check: true, settings: {username: '', password: ''}}

            fetchMock.get(`/api/trackers/tracker1.com`, result)

            const trackers = await api.trackers.tracker('tracker1.com')

            expect(trackers).to.be.eql(result)
        })

        it(`'tracker' should throw NotFound error on 404 error`, async () => {
            const responseError = {title: 'NotFound', description: `Page not found`}
            fetchMock.get(`/api/trackers/tracker1.com`, {status: 404, body: responseError})

            const error = await expect(api.trackers.tracker('tracker1.com')).to.eventually.rejectedWith(Error)

            expect(error.message).to.be.equal('NotFound')
            expect(error.description).to.be.equal('Page not found')
        })

        it(`'tracker' should throw Error error on 500 error`, async () => {
            const responseError = {title: 'Error'}
            fetchMock.get(`/api/trackers/tracker1.com`, {status: 500, body: responseError})

            const error = await expect(api.trackers.tracker('tracker1.com')).to.eventually.rejectedWith(Error)

            expect(error.message).to.be.equal('Error')
        })
    })
})
