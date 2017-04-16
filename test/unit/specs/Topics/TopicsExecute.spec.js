import Vue from 'vue'
import TopicsExecute from 'src/components/Topics/TopicsExecute'
import moment from 'moment'
import delay from 'delay'

describe('TopicsExecute.vue', () => {
    const Constructor = Vue.extend(TopicsExecute)

    it('should display loading', async () => {
        const vm = new Constructor({ propsData: { loading: true } }).$mount()

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.ok
        expect(vm.$refs.lastExecute).to.be.not.ok
        expect(vm.$refs.executeMenu).to.be.not.ok
    })

    it('should display last execute never', async () => {
        const vm = new Constructor({ propsData: { loading: false, execute: null } }).$mount()

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.not.ok
        expect(vm.$refs.lastExecute).to.be.ok
        expect(vm.$refs.executeMenu).to.be.ok

        expect(vm.$refs.lastExecute.textContent).to.contain('Last Execute')
        expect(vm.$refs.lastExecute.textContent).to.contain('never')
    })

    it('should display Execute {{tracker}} menu item', async () => {
        const vm = new Constructor({ propsData: { loading: false, execute: null, trackers: ['lostfilm.tv', 'rutor.org'] } }).$mount()

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.not.ok
        expect(vm.$refs.lastExecute).to.be.ok
        expect(vm.$refs.executeMenu).to.be.ok

        expect(vm.$refs.lastExecute.textContent).to.contain('Last Execute')
        expect(vm.$refs.lastExecute.textContent).to.contain('never')

        expect(vm.$refs.executeMenuItem).to.have.lengthOf(2)
        expect(vm.$refs.executeMenuItem[0].$el.textContent).to.contain('lostfilm.tv')
        expect(vm.$refs.executeMenuItem[1].$el.textContent).to.contain('rutor.org')
    })

    it(`click on executeAll should raise 'execute' event`, async () => {
        const vm = new Constructor({ propsData: { loading: false, execute: null, trackers: ['lostfilm.tv', 'rutor.org'] } }).$mount()

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.not.ok
        expect(vm.$refs.lastExecute).to.be.ok
        expect(vm.$refs.executeMenu).to.be.ok

        expect(vm.$refs.executeAllMenuItem).to.be.ok

        await Vue.nextTick()

        vm.$refs.executeMenu.$el.click()

        await Vue.nextTick()

        const executeRaised = new Promise(resolve => vm.$on('execute', () => resolve()))

        vm.$refs.executeAllMenuItem.$el.click()

        await Vue.nextTick()

        const delay5 = delay.reject(5)

        await Promise.race([executeRaised, delay5])
    })

    it(`click on executeTracker should raise 'executeTracker' event`, async () => {
        const vm = new Constructor({ propsData: { loading: false, execute: null, trackers: ['lostfilm.tv', 'rutor.org'] } }).$mount()

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.not.ok
        expect(vm.$refs.lastExecute).to.be.ok
        expect(vm.$refs.executeMenu).to.be.ok

        expect(vm.$refs.executeAllMenuItem).to.be.ok

        await Vue.nextTick()

        vm.$refs.executeMenu.$el.click()

        await Vue.nextTick()

        const executeRaised = new Promise(resolve => vm.$on('execute-tracker', tracker => resolve(tracker)))

        vm.$refs.executeMenuItem[1].$el.click()

        await Vue.nextTick()

        const delay5 = delay.reject(5)

        const tracker = await Promise.race([executeRaised, delay5])

        expect(tracker).to.be.equal('rutor.org')
    })

    it('should display Execute progress when executing is set', async () => {
        const vm = new Constructor({ propsData: { loading: false, execute: null } }).$mount()

        await Vue.nextTick()

        expect(vm.$refs.executingHeader).to.be.not.ok
        expect(vm.$refs.lastExecuteHeader).to.be.ok
        expect(vm.$refs.progress.$el.style.opacity).to.equal('0')

        vm.executing = true

        await Vue.nextTick()

        expect(vm.$refs.executingHeader).to.be.ok
        expect(vm.$refs.lastExecuteHeader).to.be.not.ok
        expect(vm.$refs.progress.$el.style.opacity).to.equal('1')

        vm.executingLogs = [{level: 'info', message: 'Message 1'}]

        await Vue.nextTick()

        expect(vm.$refs.executingHeader.$el.textContent).to.be.equal('Message 1')

        vm.executingLogs = [
            {level: 'info', message: 'Message 1'},
            {level: 'info', message: 'Message 2'},
            {level: 'info', message: 'Message 3'}
        ]

        await Vue.nextTick()

        expect(vm.$refs.executingHeader.$el.textContent).to.be.equal('Message 3')

        vm.executing = false

        await Vue.nextTick()

        expect(vm.$refs.executingHeader).to.be.not.ok
        expect(vm.$refs.lastExecuteHeader).to.be.ok
        expect(vm.$refs.progress.$el.style.opacity).to.equal('0')
    })

    const results = [
        {failed: 2, downloaded: 2, expectedClass: 'color-failed'},
        {failed: 0, downloaded: 2, expectedClass: 'color-downloaded'}
    ]

    for (const result of results) {
        it(`should reset Execute status during executing`, async () => {
            const lastExecute = { finish_time: '2017-02-12T22:13:45+00:00', ...result }
            const props = { loading: false, execute: lastExecute }
            const vm = new Constructor({ propsData: props }).$mount()

            await Vue.nextTick()

            expect(vm.$refs.root.className).contain(result.expectedClass)

            vm.executing = true

            await Vue.nextTick()

            expect(vm.$refs.root.className).to.be.empty
        })
    }

    describe('TopicsExecute.vue time testing', () => {
        let clock

        beforeEach(() => { clock = sinon.useFakeTimers() })
        afterEach(() => clock.restore())

        const Constructor = Vue.extend(TopicsExecute)

        it('should display last execute: at 22:13 (an hour ago)', async () => {
            clock.tick(1486940625000) // 2017-02-12T23:03:45+00:00

            const vm = new Constructor({ propsData: { loading: false, execute: { finish_time: '2017-02-12T22:13:45+00:00' } } }).$mount()

            await Vue.nextTick()

            expect(vm.$refs.loading).to.be.not.ok
            expect(vm.$refs.lastExecute).to.be.ok
            expect(vm.$refs.executeMenu).to.be.ok

            expect(vm.$refs.lastExecute.textContent).to.contain('Last Execute')
            expect(vm.$refs.lastExecute.textContent).to.contain(moment('2017-02-12T22:13:45+00:00').format('HH:mm'))
            expect(vm.$refs.lastExecute.textContent).to.contain('(an hour ago)')
        })
    })
})
