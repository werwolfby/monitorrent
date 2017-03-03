import Vue from 'vue'
import TopicsHeader from 'src/components/Topics/TopicsHeader'

describe('TopicsHeader.vue', () => {
    const Constructor = Vue.extend(TopicsHeader)

    it('should render correct content', () => {
        const vm = new Constructor().$mount()
        expect(vm.$refs.filter.$el).to.be.ok
        expect(vm.$refs.sort.$el.querySelector('select')).to.be.ok
        expect(vm.$refs.add.$el).to.be.ok
    })

    it('should have empty values by default', () => {
        const vm = new Constructor().$mount()
        expect(vm.$refs.filter.$el).to.have.property('value').equal('')
        expect(vm.$refs.sort.$el.querySelector('select')).to.have.property('value').equal('')
    })

    it('should have values equal to props', async () => {
        const props = { filter: 'lostfilm.tv', order: '-last_update' }
        const vm = new Constructor({ propsData: props }).$mount()

        await Vue.nextTick()

        expect(vm.$refs.filter.$el).to.have.property('value').equal('lostfilm.tv')
        expect(vm.$refs.sort.$el.querySelector('select')).to.have.property('value').equal('-last_update')
    })

    it('should have values equal to props', async () => {
        const props = { filter: 'lostfilm.tv', order: 'display_name' }
        const vm = new Constructor({ propsData: props }).$mount()

        await Vue.nextTick()

        expect(vm.$refs.filter.$el).to.have.property('value').equal('lostfilm.tv')
        expect(vm.$refs.sort.$el.querySelector('select')).to.have.property('value').equal('display_name')
    })

    it('wrong order should not update value', async () => {
        const props = { filter: 'title', order: 'rating' }
        const vm = new Constructor({ propsData: props }).$mount()

        await Vue.nextTick()

        expect(vm.$refs.filter.$el).to.have.property('value').equal('title')
        expect(vm.$refs.sort.$el.querySelector('select')).to.have.property('value').equal('')
    })

    it('set value to #filter should raise change-filter event', async () => {
        const vm = new Constructor().$mount()
        const changeFilterExecuted = new Promise(resolve => vm.$on('change-filter', () => resolve()))

        await Vue.nextTick()

        vm.$refs.filter.$el.value = 'title'
        vm.$refs.filter.onInput()

        const wait = ms => new Promise(resolve => setTimeout(resolve, ms))
        const raiseIn10ms = wait(10).then(() => { throw new Error('Event was not executed') })
        await Promise.race([changeFilterExecuted, raiseIn10ms])

        expect(vm.$refs.filter.$el).to.have.property('value').equal('title')
        expect(vm.$refs.sort.$el.querySelector('select')).to.have.property('value').equal('')
    })

    it('select value in #order should raise change-order event', async () => {
        const vm = new Constructor().$mount()
        const changeOrderExecuted = new Promise(resolve => vm.$on('change-order', () => resolve()))

        vm.$refs.sort.selectOption('-last_update', 'Last Update')

        await Vue.nextTick()

        const wait = ms => new Promise(resolve => setTimeout(resolve, ms))
        const raiseIn10ms = wait(10).then(() => { throw new Error('Event was not executed') })
        await Promise.race([changeOrderExecuted, raiseIn10ms])

        expect(vm.$refs.filter.$el).to.have.property('value').equal('')
        expect(vm.$refs.sort.$el.querySelector('select')).to.have.property('value').equal('-last_update')
        expect(vm.$refs.sort.$el.querySelector('select')).to.have.property('textContent').contain('Last Update')
    })

    it('click on #add should raise add-topic event', async () => {
        const vm = new Constructor().$mount()
        const changeOrderExecuted = new Promise(resolve => vm.$on('add-topic', () => resolve()))

        await Vue.nextTick()

        const buttonElement = vm.$refs.add.$el
        buttonElement.click()

        const wait = ms => new Promise(resolve => setTimeout(resolve, ms))
        const raiseIn10ms = wait(10).then(() => { throw new Error('Event was not executed') })
        await Promise.race([changeOrderExecuted, raiseIn10ms])
    })
})
