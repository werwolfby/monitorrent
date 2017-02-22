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
                { display_name: 'Topic 2 / Season 2-3', last_update: new Date(2017, 1, 18, 23, 2, 34), tracker: 'rutor.org' }
            ]
        }
        const vm = new Constructor({ propsData }).$mount()

        expect(vm.$refs.list).to.be.ok
        expect(vm.$refs.addTopics).to.be.not.ok
        expect(vm.$refs.loading).to.be.not.ok

        expect(vm.$refs.topic).to.have.lengthOf(2)

        expect(vm.$refs.topic[0].$el.textContent).to.contain(propsData.topics[0].display_name)
        expect(vm.$refs.topic[0].$el.textContent).to.contain('not specified')

        expect(vm.$refs.topic[1].$el.textContent).to.contain(propsData.topics[1].display_name)
        expect(vm.$refs.topic[1].$el.textContent).to.not.contain('not specified')
        expect(vm.$refs.topic[1].$el.textContent).to.contain('18.02.2017 23:02:34')
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

    it('should display has right menu items', async () => {
        const propsData = {
            loading: false,
            topics: [
                { display_name: 'Topic 1 / Season 1', tracker: 'losfilm.tv', last_update: null, paused: true, status: 'Ok' },
                { display_name: 'Topic 2 / Season 1', tracker: 'rutracker.org', last_update: null, paused: true, status: 'Error' },
                { display_name: 'Topic 3 / Season 1', tracker: 'rutor.org', last_update: null, paused: false, status: 'Error' },
                { display_name: 'Topic 3 / Season 1', tracker: 'hdclub.tv', last_update: null, paused: false, status: 'Ok' }
            ]
        }
        const vm = new Constructor({ propsData }).$mount()

        expect(vm.$refs.loading).to.be.not.ok
        expect(vm.$refs.list).to.be.ok
        expect(vm.$refs.addTopics).to.be.not.ok

        expect(vm.$refs.topic).to.have.lengthOf(4)

        const menuItems0 = vm.$refs.topic[0].$el.querySelectorAll('.md-list-item.md-menu-item')
        expect(menuItems0).to.have.lengthOf(4)
        expect(menuItems0[0].textContent).to.contain('Edit')
        expect(menuItems0[1].textContent).to.contain('Unpause')
        expect(menuItems0[2].textContent).to.contain('Execute').and.contain('losfilm.tv')
        expect(menuItems0[3].textContent).to.contain('Delete')
        expect(vm.$refs.topic[0].$el.className).to.contain('mt-color-paused').and.to.not.contain('mt-color-failed')

        const menuItems1 = vm.$refs.topic[1].$el.querySelectorAll('.md-list-item.md-menu-item')
        expect(menuItems1).to.have.lengthOf(4)
        expect(menuItems1[0].textContent).to.contain('Edit')
        expect(menuItems1[1].textContent).to.contain('Unpause')
        expect(menuItems1[2].textContent).to.contain('Execute').and.contain('rutracker.org')
        expect(menuItems1[3].textContent).to.contain('Delete')
        expect(vm.$refs.topic[1].$el.className).to.contain('mt-color-paused').and.to.not.contain('mt-color-failed')

        const menuItems2 = vm.$refs.topic[2].$el.querySelectorAll('.md-list-item.md-menu-item')
        expect(menuItems2).to.have.lengthOf(6)
        expect(menuItems2[0].textContent).to.contain('Edit')
        expect(menuItems2[1].textContent).to.contain('Pause')
        expect(menuItems2[2].textContent).to.contain('Reset Status')
        expect(menuItems2[3].textContent).to.contain('Execute')
        expect(menuItems2[4].textContent).to.contain('Execute').and.contain('rutor.org')
        expect(menuItems2[5].textContent).to.contain('Delete')
        expect(vm.$refs.topic[2].$el.className).to.contain('mt-color-failed').and.to.not.contain('mt-color-paused')

        const menuItems3 = vm.$refs.topic[3].$el.querySelectorAll('.md-list-item.md-menu-item')
        expect(menuItems3).to.have.lengthOf(5)
        expect(menuItems3[0].textContent).to.contain('Edit')
        expect(menuItems3[1].textContent).to.contain('Pause')
        expect(menuItems3[2].textContent).to.contain('Execute')
        expect(menuItems3[3].textContent).to.contain('Execute').and.contain('hdclub.tv')
        expect(menuItems3[4].textContent).to.contain('Delete')
        expect(vm.$refs.topic[3].$el.className).to.not.contain('mt-color-failed').and.to.not.contain('mt-color-paused')
    })
})
