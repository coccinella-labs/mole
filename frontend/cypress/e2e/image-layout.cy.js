import { MOLECULE_IMAGE } from '../fixtures/molimage'

// The image is a 400x400 PNG fetched from the real API. A 1x1 placeholder
// cannot exercise decoding or layout, because naturalWidth stays 0 until the
// browser has decoded the bytes.

const SMILES = 'CC(=O)OC1=CC=CC=C1C(=O)O'

describe('result image layout', () => {
  it('decodes and fits inside a narrow viewport', () => {
    cy.viewport(375, 812)
    cy.visit('/')
    cy.get('input[type="text"]').type(SMILES)
    cy.intercept('POST', '**/generate_molecule', {
      statusCode: 200,
      body: {
        original_smiles: SMILES,
        generated_smiles: 'CC(=O)Oc1ccccc1C(=O)O',
        molecular_image: MOLECULE_IMAGE,
        properties: { 'Molecular Weight': 180.16, LogP: 1.31 },
        requested_mutations: 3,
        successful_mutations: 3,
        failed_mutations: 0,
        mutated: true,
      },
    }).as('gen')
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
