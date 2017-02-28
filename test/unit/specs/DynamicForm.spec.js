import Vue from 'vue'
import DynamicFrom from 'src/components/DynamicForm'

describe('mtDynamicForm', () => {
    it('should render one row and 2 text inputs with default gutter (24) and username value', () => {
        const rows = [
            {
                type: 'row',
                content: [{
                    type: 'text',
                    model: 'username',
                    label: 'Username',
                    value: 'monitorrent',
                    flex: 50
                }, {
                    type: 'password',
                    model: 'password',
                    label: 'Password',
                    flex: 50
                }]
            }
        ]

        const Constructor = Vue.extend(DynamicFrom)
        const vm = new Constructor({propsData: {rows}}).$mount()

        expect(vm.$refs.row0).to.be.ok
        expect(vm.$refs.row0.$el.className).to.contain('md-gutter-24')
        expect(vm.$refs.username).to.be.ok
        expect(vm.$refs.password).to.be.ok

        expect(vm.$refs.username.$el.className).to.contain('50')
        expect(vm.$refs.password.$el.className).to.contain('50')

        expect(vm.$refs.username.$el.querySelector('.md-input').type).to.be.equal('text')
        expect(vm.$refs.username.$el.querySelector('.md-input').value).to.be.equal('monitorrent')
        expect(vm.$refs.username.$el.querySelector('label').textContent).to.be.equal('Username')

        expect(vm.$refs.password.$el.querySelector('.md-input').type).to.be.equal('password')
        expect(vm.$refs.password.$el.querySelector('label').textContent).to.be.equal('Password')
    })

    it('should render 2 rows with text and select in 1st row and password and number in 2nd and gutter = 16', () => {
        const rows = [
            {
                type: 'row',
                content: [{
                    type: 'text',
                    model: 'username',
                    label: 'Username',
                    flex: 60
                }, {
                    type: 'select',
                    model: 'quality',
                    label: 'Quality',
                    flex: 40,
                    options: ['1080', '720', 'SD']
                }]
            },
            {
                type: 'row',
                content: [{
                    type: 'text',
                    model: 'host',
                    label: 'Host',
                    flex: 70
                }, {
                    type: 'number',
                    model: 'port',
                    label: 'Port',
                    flex: 30
                }]
            }
        ]

        const Constructor = Vue.extend(DynamicFrom)
        const vm = new Constructor({propsData: {rows, gutter: 16}}).$mount()

        expect(vm.$refs.row0).to.be.ok
        expect(vm.$refs.row1).to.be.ok
        expect(vm.$refs.row0.$el.className).to.contain('md-gutter-16')
        expect(vm.$refs.row1.$el.className).to.contain('md-gutter-16')
        expect(vm.$refs.username).to.be.ok
        expect(vm.$refs.quality).to.be.ok
        expect(vm.$refs.host).to.be.ok
        expect(vm.$refs.port).to.be.ok

        expect(vm.$refs.username.$el.className).to.contain('60')
        expect(vm.$refs.quality.$el.className).to.contain('40')
        expect(vm.$refs.host.$el.className).to.contain('70')
        expect(vm.$refs.port.$el.className).to.contain('30')

        expect(vm.$refs.username.$el.querySelector('.md-input').type).to.be.equal('text')
        expect(vm.$refs.username.$el.querySelector('label').textContent).to.be.equal('Username')

        expect(vm.$refs.quality.$el.querySelector('.md-select')).to.be.ok
        const qualityOptions = vm.$refs.quality.$el.querySelectorAll('.md-option')
        expect(qualityOptions).to.have.lengthOf(3)
        expect(qualityOptions[0].textContent).to.contain('1080')
        expect(qualityOptions[1].textContent).to.contain('720')
        expect(qualityOptions[2].textContent).to.contain('SD')

        expect(vm.$refs.host.$el.querySelector('.md-input').type).to.be.equal('text')
        expect(vm.$refs.host.$el.querySelector('label').textContent).to.be.equal('Host')

        expect(vm.$refs.port.$el.querySelector('.md-input').type).to.be.equal('number')
        expect(vm.$refs.port.$el.querySelector('label').textContent).to.be.equal('Port')
    })

    it('should ignore unknown input and render one row with 1 text input and default gutter (24)', () => {
        const rows = [
            {
                type: 'row',
                content: [{
                    type: 'text',
                    model: 'username',
                    label: 'Username',
                    flex: 50
                }, {
                    type: 'unknown',
                    model: 'password',
                    label: 'Password',
                    flex: 50
                }]
            }
        ]

        const Constructor = Vue.extend(DynamicFrom)
        const vm = new Constructor({propsData: {rows}}).$mount()

        expect(vm.$refs.row0).to.be.ok
        expect(vm.$refs.row0.$el.className).to.contain('md-gutter-24')
        expect(vm.$refs.username).to.be.ok
        expect(vm.$refs.password).to.be.not.ok

        expect(vm.$refs.username.$el.className).to.contain('50')

        expect(vm.$refs.username.$el.querySelector('.md-input').type).to.be.equal('text')
        expect(vm.$refs.username.$el.querySelector('label').textContent).to.be.equal('Username')
    })
})
