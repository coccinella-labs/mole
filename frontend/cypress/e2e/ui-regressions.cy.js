// Regression cover for behaviour that already worked, plus layout at real
// viewport sizes.

import { MOLECULE_IMAGE } from '../fixtures/molimage'

const SMILES = 'CC(=O)OC1=CC=CC=C1C(=O)O'

// The API returns bare base64; App.js builds the data URI from it. Passing a
// complete data URI here would nest the scheme and the image would never decode.
const payload = (over) => ({
  original_smiles: SMILES,
  generated_smiles: 'CC(=O)Oc1ccccc1C(=O)O',
  molecular_image: MOLECULE_IMAGE,
  properties: { 'Molecular Weight': 180.16, LogP: 1.31 },
  requested_mutations: 3,
  successful_mutations: 3,
  failed_mutations: 0,
  mutated: true,
  ...over,
})

describe('unchanged behaviour: errors a user can reach', () => {
  beforeEach(() => {
    cy.visit('/')
    cy.get('input[type="text"]').type(SMILES)
  })

  it('blocks an empty SMILES without calling the API', () => {
    cy.visit('/')
    cy.intercept('POST', '**/generate_molecule').as('gen')
    cy.get('input[type="number"]').should('have.value', '3')
    cy.get('button').contains('Generate Molecule').click()
    cy.contains('Please enter a base molecule').should('be.visible')
    cy.get('@gen.all').should('have.length', 0)
  })

  it('reports an unreachable backend in plain language', () => {
    cy.intercept('POST', '**/generate_molecule', { forceNetworkError: true }).as('dead')
    cy.get('button').contains('Generate Molecule').click()
    cy.wait('@dead')
    cy.contains('cannot reach the backend').should('be.visible')
  })

  it('disables the button while a request is in flight and re-enables it after', () => {
    // Hold the response with an explicitly returned promise. A promise created
    // outside the handler and resolved from test code does not keep the request
    // pending, so the previous version observed the response and the success
    // toast, whose close control is a second <button> on the page.
    cy.intercept('POST', '**/generate_molecule', () => {
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({ statusCode: 200, body: payload() })
        }, 1500)
      })
    }).as('gen')

    cy.contains('button', 'Generate Molecule').click()
    cy.contains('button', 'Generating...').should('be.visible').and('be.disabled')
    cy.wait('@gen')
    cy.contains('button', 'Generate Molecule').should('not.be.disabled')
  })
})

describe('unchanged behaviour: the zero-mutation notice', () => {
  it('renders when the API reports mutated=false, from a controlled response', () => {
    cy.visit('/')
    cy.get('input[type="text"]').type(SMILES)
    cy.intercept('POST', '**/generate_molecule', {
      statusCode: 200,
      body: payload({
        requested_mutations: 4,
        successful_mutations: 0,
        failed_mutations: 4,
        mutated: false,
      }),
    }).as('gen')
    cy.get('button').contains('Generate Molecule').click()
    cy.wait('@gen')
    cy.contains('Mutations Applied').should('be.visible')
    cy.contains('0 of 4 applied').should('be.visible')
    cy.contains('No mutation could be applied').should('be.visible')
    cy.contains('unchanged from the input').should('be.visible')
  })

  it('does not render when the API reports mutated=true', () => {
    cy.visit('/')
    cy.get('input[type="text"]').type(SMILES)
    cy.intercept('POST', '**/generate_molecule', {
      statusCode: 200,
      body: payload({ mutated: true }),
    }).as('gen')
    cy.get('button').contains('Generate Molecule').click()
    cy.wait('@gen')
    cy.contains('No mutation could be applied').should('not.exist')
  })
})

describe('layout across viewports', () => {
  const sizes = [
    { name: '375', w: 375, h: 812 },
    { name: '768', w: 768, h: 1024 },
    { name: '1440', w: 1440, h: 900 },
  ]

  sizes.forEach(({ name, w, h }) => {
    it(`does not overflow horizontally at ${name}px`, () => {
      cy.viewport(w, h)
      cy.visit('/')
      cy.get('input[type="text"]').should('be.visible')
      cy.document().then((doc) => {
        expect(
          doc.documentElement.scrollWidth,
          `scrollWidth ${doc.documentElement.scrollWidth} exceeds clientWidth ${doc.documentElement.clientWidth}`
        ).to.be.at.most(doc.documentElement.clientWidth + 1)
      })
    })

    it(`keeps both controls reachable at ${name}px`, () => {
      cy.viewport(w, h)
      cy.visit('/')
      cy.get('input[type="text"]').should('be.visible')
      cy.get('input[type="number"]').should('be.visible')
      cy.get('button').contains('Generate Molecule').should('be.visible')
    })
  })

  it('keeps the rendered image inside a narrow viewport', () => {
    cy.viewport(375, 812)
    cy.visit('/')
    cy.get('input[type="text"]').type(SMILES)
    cy.intercept('POST', '**/generate_molecule', { statusCode: 200, body: payload() }).as('gen')
    cy.get('button').contains('Generate Molecule').click()
    cy.wait('@gen')
    cy.get('img').should('be.visible')
    cy.get('img').should(($img) => {
      expect($img[0].naturalWidth, 'image did not decode').to.be.greaterThan(0)
    })
    cy.get('img').then(($img) => {
      const rect = $img[0].getBoundingClientRect()
      expect(rect.width, `image width ${rect.width} exceeds the viewport`).to.be.at.most(376)
    })
  })
})

describe('document basics', () => {
  it('declares a language', () => {
    cy.visit('/')
    cy.get('html').should('have.attr', 'lang')
  })

  it('shows a heading for orientation', () => {
    cy.visit('/')
    cy.contains('h1, h2, h3', 'Mole').should('be.visible')
  })

  it('uses a real button element for the primary action', () => {
    cy.visit('/')
    cy.get('button').contains('Generate Molecule').should('match', 'button')
  })
})
