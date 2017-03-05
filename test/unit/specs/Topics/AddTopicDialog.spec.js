import Vue from 'vue'
import * as api from 'src/api/monitorrent'
import AddTopicDialog from 'src/components/Topics/AddTopicDialog'

describe('AddTopicDialog.vue', () => {
    const defaultClientResult = {
        fields: {},
        name: 'downloader',
        settings: {
            path: '/path/to/folder'
        }
    }
    const parseUrlResult = {
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

    function createPromiseResolve (value) {
        // For some cases Promise.resolve doesn't work as expected under PhantomJS
        return new Promise(resolve => setTimeout(() => resolve(value)))
    }

    let defaultClientStub = null
    function createDefaultClientStub (value = defaultClientResult) {
        defaultClientStub = sinon.stub(api.default, 'defaultClient', () => createPromiseResolve(value))
    }

    let parseUrlStub = null
    function createParseUrlStub (value = parseUrlResult) {
        parseUrlStub = sinon.stub(api.default, 'parseUrl', () => createPromiseResolve(value))
    }

    afterEach(function () {
        if (defaultClientStub != null) {
            defaultClientStub.restore()
            defaultClientStub = null
        }

        if (parseUrlStub != null) {
            parseUrlStub.restore()
            parseUrlStub = null
        }
    })

    const Constructor = Vue.extend(AddTopicDialog)

    it('call to defaultClient should set status', async function () {
        const vm = new Constructor().$mount()
        createDefaultClientStub()

        await Vue.nextTick()

        expect(vm.$refs.addTopicDialog).to.be.ok

        await vm.defaultClient()

        expect(vm.additionalFields.downloadDir.support).to.be.equal(false)
        expect(vm.additionalFields.downloadDir.path).to.be.empty
        expect(vm.additionalFields.downloadDir.defaultClientName).to.be.equal('downloader')

        expect(defaultClientStub).to.have.been.called
    })

    it('call to parseUrl should set status', async function () {
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(vm.$refs.addTopicDialog).to.be.ok

        createParseUrlStub()

        await vm.parseUrl()

        const url = 'https://lostfilm.tv/series/TV_Show/seasons'
        vm.topic.url = url

        await vm.parseUrl()

        expect(vm.topic.parsed).to.be.ok
        expect(vm.topic.form).to.be.eql({rows: parseUrlResult.form, model: parseUrlResult.settings})

        expect(parseUrlStub).to.have.been.calledWith(url)
    })

    it('call to open should make dialog visible and call defaultClient', async function () {
        const vm = new Constructor().$mount()
        createDefaultClientStub()

        await Vue.nextTick()

        expect(document.body.contains(vm.$el)).to.be.false

        await vm.open()
        await Vue.nextTick()
        expect(document.body.contains(vm.$el)).to.be.true

        expect(defaultClientStub).to.have.been.called
    })

    it(`call to open and then close should make dialog visible and then invisible`, async function () {
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(document.body.contains(vm.$el)).to.be.false

        createDefaultClientStub()

        await vm.open()
        await Vue.nextTick()
        expect(document.body.contains(vm.$el)).to.be.true

        vm.close()
        await Vue.nextTick()
        await new Promise(resolve => setTimeout(resolve, 500))

        expect(document.body.contains(vm.$el)).to.be.false
    })

    it(`should allow to press 'add' button`, async function () {
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(vm.$refs.addTopicDialog).to.be.ok

        createDefaultClientStub()
        createParseUrlStub()

        await vm.open()
        await Vue.nextTick()

        expect(vm.topic.parsed).to.be.false
        expect(vm.additionalFields.downloadDir.complete).to.be.ok
        expect(vm.complete).to.be.false

        const url = 'https://lostfilm.tv/series/TV_Show/seasons'
        vm.topic.url = url

        await vm.parseUrl()

        expect(vm.topic.parsed).to.be.ok
        expect(vm.topic.form).to.be.eql({rows: parseUrlResult.form, model: parseUrlResult.settings})

        expect(parseUrlStub).to.have.been.calledWith(url)

        expect(vm.topic.parsed).to.be.ok
        expect(vm.additionalFields.downloadDir.complete).to.be.ok
        expect(vm.complete).to.be.ok
    })

    class Deferred {
        constructor () {
            this.promise = new Promise((resolve, reject) => {
                this.resolve = resolve
                this.reject = reject
            })
        }

        resolve () {
            this.resolve(arguments)
        }

        reject () {
            this.reject(arguments)
        }
    }

    it(`should display loading for download dir after open and hide on finish`, async function () {
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(vm.$refs.addTopicDialog).to.be.ok

        const defaultClientDeferred = new Deferred()
        defaultClientStub = sinon.stub(api.default, 'defaultClient', () => defaultClientDeferred.promise)

        expect(vm.additionalFields.downloadDir.loading).to.be.false

        const openPromise = vm.open()

        expect(vm.additionalFields.downloadDir.loading).to.be.true

        defaultClientDeferred.resolve(defaultClientResult)

        await openPromise
        await Vue.nextTick()

        expect(vm.additionalFields.downloadDir.loading).to.be.false
    })

    it(`should display loading for parse url after set topic.url and hide on finish`, async function () {
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(vm.$refs.addTopicDialog).to.be.ok

        createDefaultClientStub()
        const parseUrlDeferred = new Deferred()
        parseUrlStub = sinon.stub(api.default, 'parseUrl', () => parseUrlDeferred.promise)

        expect(vm.topic.loading).to.be.false

        const url = 'https://lostfilm.tv/series/TV_Show/seasons'
        vm.topic.url = url

        await Vue.nextTick()

        expect(vm.topic.loading).to.be.true

        parseUrlDeferred.resolve(parseUrlResult)
        await Vue.nextTick()

        expect(vm.topic.loading).to.be.false
    })

    it(`click 'add' should raise add-topic event`, async function () {
        const vm = new Constructor().$mount()

        const addTopicEventFinished = new Promise(resolve => vm.$on('add-topic', resolve))

        await Vue.nextTick()

        expect(vm.$refs.addTopicDialog).to.be.ok

        createDefaultClientStub()
        createParseUrlStub()

        await vm.open()
        await Vue.nextTick()

        const url = 'https://lostfilm.tv/series/TV_Show/seasons'
        vm.topic.url = url

        await vm.parseUrl()
        await Vue.nextTick()

        expect(vm.complete).to.be.ok

        vm.$refs.add.$el.click()

        await Vue.nextTick()
        await new Promise(resolve => setTimeout(resolve))

        const raiseIn10ms = wait(10).then(() => { throw new Error('Event was not executed') })
        await Promise.race([addTopicEventFinished, raiseIn10ms])
    })
})
