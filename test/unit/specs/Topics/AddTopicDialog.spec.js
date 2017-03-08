import Vue from 'vue'
import * as api from 'src/api/monitorrent'
import AddTopicDialog from 'src/components/Topics/AddTopicDialog'
import Deferred from 'es2015-deferred'

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

    const sandbox = sinon.sandbox.create()

    let defaultClientStub = null
    function createDefaultClientStub (value = defaultClientResult) {
        defaultClientStub = sandbox.stub(api.default, 'defaultClient', () => createPromiseResolve(value))
    }

    let parseUrlStub = null
    function createParseUrlStub (value = parseUrlResult) {
        parseUrlStub = sandbox.stub(api.default, 'parseUrl', () => createPromiseResolve(value))
    }

    const wait = ms => new Promise(resolve => setTimeout(resolve, ms))

    afterEach(function () {
        sandbox.restore()
    })

    const Constructor = Vue.extend(AddTopicDialog)

    it('call to defaultClient with supported downloadDir should not show download dir error and not disabled input', async function () {
        const vm = new Constructor().$mount()
        const supportedDefaultClientResult = {...defaultClientResult, ...{fields: {download_dir: '/path/to/dir'}, name: 'transmission'}}
        createDefaultClientStub(supportedDefaultClientResult)

        await Vue.nextTick()

        expect(vm.$refs.addTopicDialog).to.be.ok
        expect(vm.$refs.downloadDirNotSupportedError).to.be.not.ok
        expect(vm.$refs.downloadDirError).to.be.not.ok

        await vm.defaultClient()
        await Vue.nextTick()

        expect(vm.additionalFields.downloadDir.support).to.be.equal(true)
        expect(vm.additionalFields.downloadDir.path).to.be.equal(supportedDefaultClientResult.fields.download_dir)
        expect(vm.additionalFields.downloadDir.defaultClientName).to.be.equal('transmission')

        expect(defaultClientStub).to.have.been.called
        expect(vm.$refs.downloadDirNotSupportedError).to.be.not.ok
        expect(vm.$refs.downloadDirError).to.be.not.ok

        expect(vm.$refs.downloadDirInput.disabled).to.be.false
        expect(vm.$refs.downloadDirInput.value).to.be.equal(supportedDefaultClientResult.fields.download_dir)
    })

    it('call to defaultClient with not supported downloadDir should show download dir error and disabled input', async function () {
        const vm = new Constructor().$mount()
        createDefaultClientStub()

        await Vue.nextTick()

        expect(vm.$refs.addTopicDialog).to.be.ok
        expect(vm.$refs.downloadDirNotSupportedError).to.be.not.ok
        expect(vm.$refs.downloadDirError).to.be.not.ok

        await vm.defaultClient()
        await Vue.nextTick()

        expect(vm.additionalFields.downloadDir.support).to.be.equal(false)
        expect(vm.additionalFields.downloadDir.path).to.be.empty
        expect(vm.additionalFields.downloadDir.defaultClientName).to.be.equal('downloader')

        expect(defaultClientStub).to.have.been.called
        expect(vm.$refs.downloadDirNotSupportedError).to.be.ok
        expect(vm.$refs.downloadDirError).to.be.not.ok

        expect(vm.$refs.downloadDirInput.disabled).to.be.true
        expect(vm.$refs.downloadDirInput.value).to.be.empty
    })

    it('failed call with unknown error to defaultClient should show download dir error and disabled input', async function () {
        const vm = new Constructor().$mount()
        const defaultClientDeferred = new Deferred()
        defaultClientStub = sandbox.stub(api.default, 'defaultClient', () => defaultClientDeferred.promise)
        const consoleErrorStub = sandbox.stub(console, 'error')

        await Vue.nextTick()

        expect(vm.$refs.addTopicDialog).to.be.ok
        expect(vm.$refs.downloadDirNotSupportedError).to.be.not.ok
        expect(vm.$refs.downloadDirError).to.be.not.ok

        const openPromise = vm.open()
        const error = new Error('failed to get default client')
        defaultClientDeferred.reject(error)
        await openPromise
        await Vue.nextTick()

        expect(vm.additionalFields.downloadDir.support).to.be.equal(false)
        expect(vm.additionalFields.downloadDir.path).to.be.empty
        expect(vm.additionalFields.downloadDir.defaultClientName).to.be.empty
        expect(vm.additionalFields.downloadDir.complete).to.be.false

        expect(defaultClientStub).to.have.been.calledOnce
        expect(defaultClientStub).to.have.been.called

        expect(consoleErrorStub).to.have.been.calledOnce
        expect(consoleErrorStub.lastCall.args[0]).to.equal(error)

        expect(vm.$refs.downloadDirNotSupportedError).to.be.not.ok
        expect(vm.$refs.downloadDirError).to.be.ok

        expect(vm.$refs.downloadDirInput.disabled).to.be.true
        expect(vm.$refs.downloadDirInput.value).to.be.empty
    })

    it('call to parseUrl should set status', async function () {
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(vm.$refs.addTopicDialog).to.be.ok

        createParseUrlStub()
        const parseUrlSpy = sandbox.spy(vm, 'parseUrl')

        const url = 'https://lostfilm.tv/series/TV_Show/seasons'
        vm.topic.url = url

        await Vue.nextTick()
        await parseUrlSpy.lastCall.returnValue

        expect(vm.topic.parsed).to.be.ok
        expect(vm.topic.form).to.be.eql({rows: parseUrlResult.form, model: parseUrlResult.settings})

        expect(parseUrlStub).to.have.been.calledWith(url)
    })

    it('failed call with CantParse error to parseUrl should set error', async function () {
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(vm.$refs.addTopicDialog).to.be.ok
        expect(vm.$refs.topicError).to.be.not.ok

        const parseUrlDeferred = new Deferred()
        parseUrlStub = sandbox.stub(api.default, 'parseUrl', () => parseUrlDeferred.promise)

        const parseUrlSpy = sandbox.spy(vm, 'parseUrl')

        const url = 'https://lostfilm.tv/series/TV_Show/seasons'
        vm.topic.url = url

        expect(parseUrlSpy).have.not.been.called

        await Vue.nextTick()

        expect(parseUrlSpy).have.been.calledOnce

        const error = new Error(`CantParse`)
        error.description = `Can't parse topic: ${url}`
        parseUrlDeferred.reject(error)

        await parseUrlSpy.lastCall.returnValue
        await Vue.nextTick()

        expect(parseUrlStub).to.have.been.calledWith(url)

        expect(vm.topic.parsed).to.be.false
        expect(vm.topic.form).to.be.eql({rows: []})
        expect(vm.topic.error).to.be.equal(error.description)

        expect(vm.$refs.topicError).to.be.ok
    })

    it('failed call with unknow error to parseUrl should set error and print error to console', async function () {
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(vm.$refs.addTopicDialog).to.be.ok

        const parseUrlDeferred = new Deferred()
        parseUrlStub = sandbox.stub(api.default, 'parseUrl', () => parseUrlDeferred.promise)

        const parseUrlSpy = sandbox.spy(vm, 'parseUrl')

        const url = 'https://lostfilm.tv/series/TV_Show/seasons'
        vm.topic.url = url

        expect(parseUrlSpy).have.not.been.called

        await Vue.nextTick()

        expect(parseUrlSpy).have.been.calledOnce

        const consoleErrorStub = sandbox.stub(console, 'error')

        const error = new Error(`NetworkError`)
        parseUrlDeferred.reject(error)

        await parseUrlSpy.lastCall.returnValue

        expect(vm.topic.parsed).to.be.false
        expect(vm.topic.form).to.be.eql({rows: []})
        expect(vm.topic.error).to.contain(error.message)

        expect(parseUrlSpy).have.been.calledOnce
        expect(parseUrlStub).have.been.calledWith(url)

        expect(consoleErrorStub).have.been.calledOnce
        expect(consoleErrorStub.lastCall.args[0]).to.equal(error)
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

        const parseUrlSpy = sandbox.spy(vm, 'parseUrl')

        await vm.open()
        await Vue.nextTick()

        // parseUrl already called because open() set topic.url to null
        parseUrlSpy.reset()

        expect(vm.topic.parsed).to.be.false
        expect(vm.additionalFields.downloadDir.complete).to.be.ok
        expect(vm.complete).to.be.false

        const url = 'https://lostfilm.tv/series/TV_Show/seasons'
        vm.topic.url = url

        await Vue.nextTick()

        expect(parseUrlSpy).have.been.calledOnce

        await parseUrlSpy.lastCall.returnValue

        expect(vm.topic.parsed).to.be.ok
        expect(vm.topic.form).to.be.eql({rows: parseUrlResult.form, model: parseUrlResult.settings})

        expect(parseUrlStub).to.have.been.calledWith(url)

        expect(vm.topic.parsed).to.be.ok
        expect(vm.additionalFields.downloadDir.complete).to.be.ok
        expect(vm.complete).to.be.ok
    })

    it(`should display loading for download dir after open and hide on finish`, async function () {
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(vm.$refs.addTopicDialog).to.be.ok

        const defaultClientDeferred = new Deferred()
        defaultClientStub = sandbox.stub(api.default, 'defaultClient', () => defaultClientDeferred.promise)

        expect(vm.additionalFields.downloadDir.loading).to.be.false

        const openPromise = vm.open()
        await Vue.nextTick()

        expect(vm.additionalFields.downloadDir.loading).to.be.true
        expect(vm.$refs.downloadDirProgress.$el.style.opacity).to.equal('1')

        defaultClientDeferred.resolve(defaultClientResult)

        await openPromise
        await Vue.nextTick()

        expect(vm.additionalFields.downloadDir.loading).to.be.false
        expect(vm.$refs.downloadDirProgress.$el.style.opacity).to.equal('0')
    })

    it(`should display loading for url after set topic url and hide on finish`, async function () {
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(vm.$refs.addTopicDialog).to.be.ok

        const parseUrlDeferred = new Deferred()
        parseUrlStub = sandbox.stub(api.default, 'parseUrl', () => parseUrlDeferred.promise)

        expect(vm.topic.loading).to.be.false

        const parseUrlSpy = sandbox.spy(vm, 'parseUrl')

        const url = 'https://lostfilm.tv/series/TV_Show/seasons'
        vm.topic.url = url

        await Vue.nextTick()

        expect(parseUrlSpy).have.been.calledOnce

        expect(vm.topic.loading).to.be.true
        expect(vm.$refs.topicProgress.$el.style.opacity).to.equal('1')

        parseUrlDeferred.resolve(parseUrlResult)

        await parseUrlSpy.lastCall.returnValue
        await Vue.nextTick()

        expect(vm.topic.loading).to.be.false
        expect(vm.$refs.topicProgress.$el.style.opacity).to.equal('0')
    })

    it(`should display loading for parse url after set topic.url and hide on finish`, async function () {
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(vm.$refs.addTopicDialog).to.be.ok

        createDefaultClientStub()
        const parseUrlDeferred = new Deferred()
        parseUrlStub = sandbox.stub(api.default, 'parseUrl', () => parseUrlDeferred.promise)

        expect(vm.topic.loading).to.be.false

        const url = 'https://lostfilm.tv/series/TV_Show/seasons'
        vm.topic.url = url

        await Vue.nextTick()

        expect(vm.topic.loading).to.be.true

        parseUrlDeferred.resolve(parseUrlResult)
        await Vue.nextTick()

        expect(vm.topic.loading).to.be.false
    })

    it(`click 'add' should raise add-topic event with correct model`, async function () {
        const vm = new Constructor().$mount()

        const addTopicEventFinished = new Promise(resolve => vm.$on('add-topic', resolve))

        await Vue.nextTick()

        expect(vm.$refs.addTopicDialog).to.be.ok

        createDefaultClientStub()
        createParseUrlStub()

        const parseUrlSpy = sandbox.spy(vm, 'parseUrl')

        await vm.open()
        await Vue.nextTick()

        const url = 'https://lostfilm.tv/series/TV_Show/seasons'
        vm.topic.url = url

        await Vue.nextTick()
        await parseUrlSpy.lastCall.returnValue

        expect(vm.complete).to.be.ok

        await Vue.nextTick()

        vm.$refs.add.$el.click()

        await Vue.nextTick()

        const raiseIn10ms = wait(10).then(() => { throw new Error('Event was not executed') })
        await Promise.race([addTopicEventFinished, raiseIn10ms])

        const result = await addTopicEventFinished

        expect(result.url).to.be.equal(url)
        expect(result.settings.display_name).to.be.equal('Табу / Taboo')
        expect(result.settings.quality).to.be.equal('720p')
        expect(result.settings.download_dir).to.be.null
    })

    it(`update model and click 'add' should raise add-topic event correct model`, async function () {
        const vm = new Constructor().$mount()

        const addTopicEventFinished = new Promise(resolve => vm.$on('add-topic', resolve))

        await Vue.nextTick()

        expect(vm.$refs.addTopicDialog).to.be.ok

        const supportedDefaultClientResult = {...defaultClientResult, ...{fields: {download_dir: '/path/to/dir'}, name: 'transmission'}}
        createDefaultClientStub(supportedDefaultClientResult)
        createParseUrlStub()

        const parseUrlSpy = sandbox.spy(vm, 'parseUrl')

        await vm.open()
        await Vue.nextTick()

        const url = 'https://lostfilm.tv/series/TV_Show/seasons'
        vm.topic.url = url

        await Vue.nextTick()
        await parseUrlSpy.lastCall.returnValue

        expect(vm.complete).to.be.ok

        await Vue.nextTick()

        vm.$refs.dynamicForm.model.display_name = 'Taboo'
        vm.$refs.dynamicForm.model.quality = '1080p'
        vm.additionalFields.downloadDir.path = '/path/to/dir/custom'

        await Vue.nextTick()

        vm.$refs.add.$el.click()

        await Vue.nextTick()

        const raiseIn10ms = wait(10).then(() => { throw new Error('Event was not executed') })
        await Promise.race([addTopicEventFinished, raiseIn10ms])

        const result = await addTopicEventFinished

        expect(result.url).to.be.equal(url)
        expect(result.settings.display_name).to.be.equal('Taboo')
        expect(result.settings.quality).to.be.equal('1080p')
        expect(result.settings.download_dir).to.be.equal('/path/to/dir/custom')
    })

    it(`update model without download_dir and click 'add' should raise add-topic event correct model`, async function () {
        const vm = new Constructor().$mount()

        const addTopicEventFinished = new Promise(resolve => vm.$on('add-topic', resolve))

        await Vue.nextTick()

        expect(vm.$refs.addTopicDialog).to.be.ok

        const supportedDefaultClientResult = {...defaultClientResult, ...{fields: {download_dir: '/path/to/dir'}, name: 'transmission'}}
        createDefaultClientStub(supportedDefaultClientResult)
        createParseUrlStub()

        const parseUrlSpy = sandbox.spy(vm, 'parseUrl')

        await vm.open()
        await Vue.nextTick()

        const url = 'https://lostfilm.tv/series/TV_Show/seasons'
        vm.topic.url = url

        await Vue.nextTick()
        await parseUrlSpy.lastCall.returnValue

        expect(vm.complete).to.be.ok

        await Vue.nextTick()

        vm.$refs.dynamicForm.model.display_name = 'Taboo'
        vm.$refs.dynamicForm.model.quality = '1080p'

        await Vue.nextTick()

        vm.$refs.add.$el.click()

        await Vue.nextTick()

        const raiseIn10ms = wait(10).then(() => { throw new Error('Event was not executed') })
        await Promise.race([addTopicEventFinished, raiseIn10ms])

        const result = await addTopicEventFinished

        expect(result.url).to.be.equal(url)
        expect(result.settings.display_name).to.be.equal('Taboo')
        expect(result.settings.quality).to.be.equal('1080p')
        expect(result.settings.download_dir).to.be.null
    })
})
