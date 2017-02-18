import Vue from 'vue'
import TopicsList from 'src/components/Topics/TopicsList'

describe('TopicsList.vue', () => {
    const Constructor = Vue.extend(TopicsList)

    it('should display loading with default props', () => {
        const vm = new Constructor().$mount()

        expect(vm.$el.textContent).to.contain('Loading...')

        expect(vm.$refs.list).to.be.not.ok
        expect(vm.$refs.addTopics).to.be.not.ok
        expect(vm.$refs.loading).to.be.ok
        expect(vm.$refs.loading.$el.textContent).to.contain('Loading...')
    })

    it('should display loading with loading = true', () => {
        const propsData = { loading: true }
        const vm = new Constructor({ propsData }).$mount()

        expect(vm.$el.textContent).to.contain('Loading...')

        expect(vm.$refs.list).to.be.not.ok
        expect(vm.$refs.addTopics).to.be.not.ok
        expect(vm.$refs.loading).to.be.ok
        expect(vm.$refs.loading.$el.textContent).to.contain('Loading...')
    })

    it('should display loading with loading = true even with topics', () => {
        const propsData = {
            loading: true,
            topics: [
                { display_name: 'Topic 1 / Season 1', last_update: null },
                { display_name: 'Topic 1 / Season 1', last_update: null }
            ]
        }
        const vm = new Constructor({ propsData }).$mount()

        expect(vm.$el.textContent).to.contain('Loading...')

        expect(vm.$refs.list).to.be.not.ok
        expect(vm.$refs.addTopics).to.be.not.ok
        expect(vm.$refs.loading).to.be.ok

        expect(vm.$refs.loading.$el.textContent).to.contain('Loading...')
    })

    it('should display topics with loading = false and with topics', () => {
        const propsData = {
            loading: false,
            topics: [
                { display_name: 'Topic 1 / Season 1', last_update: null, tracker: 'lostfilm.tv' },
                { display_name: 'Topic 2 / Season 2-3', last_update: null, tracker: 'rutor.org' }
            ]
        }
        const vm = new Constructor({ propsData }).$mount()

        expect(vm.$refs.list).to.be.ok
        expect(vm.$refs.addTopics).to.be.not.ok
        expect(vm.$refs.loading).to.be.not.ok

        expect(vm.$refs.topic).to.have.lengthOf(2)

        expect(vm.$refs.topic[0].$el.textContent).to.contain(propsData.topics[0].display_name)
        expect(vm.$refs.topic[1].$el.textContent).to.contain(propsData.topics[1].display_name)
    })

    it('should display "add topics and press execute" with loading = false and empty topics array', async () => {
        const propsData = {
            loading: false,
            topics: []
        }
        const vm = new Constructor({ propsData }).$mount()

        expect(vm.$refs.loading).to.be.not.ok
        expect(vm.$refs.list).to.be.not.ok
        expect(vm.$refs.addTopics).to.be.ok

        expect(vm.$refs.addTopics.$el.textContent).to.contain('Add torrent and press execute')
    })

    it('should display "add topics and press execute" with loading = false and null topics array', async () => {
        const propsData = {
            loading: false,
            topics: null
        }
        const vm = new Constructor({ propsData }).$mount()

        expect(vm.$refs.loading).to.be.not.ok
        expect(vm.$refs.list).to.be.not.ok
        expect(vm.$refs.addTopics).to.be.ok

        expect(vm.$refs.addTopics.$el.textContent).to.contain('Add torrent and press execute')
    })
})
