// A SMILES string is a single unbroken token, so it offers the browser no place
// to wrap. When the two SMILES values sat in a two-column grid whose items had
// no min-w-0, each item refused to shrink below its content and the text painted
// outside its track into the neighbouring column. These tests measure the value
// boxes directly: a box whose scrollWidth exceeds its clientWidth is text that
// has escaped the layout.

const BASE = 'CC(=O)OC1=CC=CC=C1C(=O)O'
// Long enough that it cannot fit one column at the default width.
const LONG = 'CC(=O)Oc1cc(Br)#ccc1C(=O)OCl'
const PNG =
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='

const respond = () =>
  cy.intercept('POST', '**/generate_molecule', {
    statusCode: 200,
    body: {
      original_smiles: BASE,
      generated_smiles: LONG,
      molecular_image: PNG,
      properties: { 'Molecular Weight': 292.49, LogP: 2.49 },
      requested_mutations: 3,
      successful_mutations: 3,
      failed_mutations: 0,
      mutated: true,
    },
  })

const generate = () => {
  cy.visit('/')
  cy.get('input[type="text"]').type(BASE)
  respond().as('gen')
  cy.get('button').contains('Generate Molecule').click()
  cy.wait('@gen')
}

// The value paragraphs sit directly under their labels in the result card.
const originalValue = () => cy.contains('strong', 'Original SMILES:').parent().find('p')
const generatedValue = () => cy.contains('strong', 'Generated SMILES:').parent().find('p')

const fitsInsideItsBox = (selector) =>
  selector().should(($p) => {
    expect(
      $p[0].scrollWidth,
      `text overflows its box: scrollWidth ${$p[0].scrollWidth} vs clientWidth ${$p[0].clientWidth}`
    ).to.be.at.most($p[0].clientWidth + 1)
  })

describe('a generated molecule with long SMILES', () => {
  it('keeps the original SMILES inside its column', () => {
    generate()
    fitsInsideItsBox(originalValue)
  })

  it('keeps the generated SMILES inside its column', () => {
    generate()
    fitsInsideItsBox(generatedValue)
  })

  it('keeps the whole result card within its container', () => {
    generate()
    cy.get('div.bg-gray-50').first().then(($card) => {
      expect(
        $card[0].scrollWidth,
        `card overflows: scrollWidth ${$card[0].scrollWidth} vs clientWidth ${$card[0].clientWidth}`
      ).to.be.at.most($card[0].clientWidth + 1)
    })
  })

  it('stacks the two values instead of overflowing on a phone width', () => {
    cy.viewport(375, 812)
    generate()
    fitsInsideItsBox(originalValue)
    fitsInsideItsBox(generatedValue)
    cy.contains('strong', 'Generated SMILES:')
      .parent()
      .then(($right) => {
        cy.contains('strong', 'Original SMILES:')
          .parent()
          .then(($left) => {
            expect(
              $right[0].getBoundingClientRect().top,
              'the second value did not stack below the first'
            ).to.be.at.least($left[0].getBoundingClientRect().bottom - 1)
          })
      })
  })
})
