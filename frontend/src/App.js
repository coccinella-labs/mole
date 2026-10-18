import React, { useState } from 'react';
import axios from 'axios';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Configure axios base URL and auth
const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
const apiKey = process.env.REACT_APP_API_KEY;

// Mirrors MAX_MUTATIONS_PER_REQUEST in backend/src/main.py, which answers a
// larger request with a 400. The API accepts 0 through this value: zero is a
// legitimate request that returns the input unchanged, so the lower bound here
// is 0 rather than 1.
const MAX_MUTATIONS = 10;

axios.defaults.baseURL = backendUrl;
if (apiKey) {
  axios.defaults.headers.common['Authorization'] = `Bearer ${apiKey}`;
}

/**
 * Turn an axios failure into something a person can act on.
 *
 * A malformed SMILES, a rejected API key and an unreachable backend are three
 * different problems, and reporting all three as 'Failed to generate molecule'
 * left the real reason in the console only.
 */
function describeError(error) {
  if (axios.isAxiosError(error)) {
    const { response } = error;
    if (!response) {
      return 'cannot reach the backend';
    }
    const detail = response.data && response.data.detail;
    if (typeof detail === 'string' && detail) {
      return detail;
    }
    // FastAPI answers a request-schema violation with 422 and a list of error
    // objects rather than a sentence, so the string check above is false and
    // the reason was being replaced by the bare status code. Read the msg
    // fields so the actual cause reaches the person.
    if (Array.isArray(detail) && detail.length) {
      const messages = detail
        .map((item) => (item && typeof item.msg === 'string' ? item.msg : null))
        .filter(Boolean);
      if (messages.length) {
        return messages.join('; ');
      }
    }
    return `request failed with status ${response.status}`;
  }
  return error.message || 'unexpected error';
}

function App() {
  const [baseMolecule, setBaseMolecule] = useState('');
  // Held as the raw string the user typed, not as a number. Clearing the field is
  // an ordinary edit, and parseInt('') is NaN, which JSON.stringify writes as
  // null and the API rejects with a 422. Keeping the string tells an empty edit
  // apart from a deliberate 0, which parseInt(value) || 0 would not.
  const [mutationsInput, setMutationsInput] = useState('3');
  const [generatedMolecule, setGeneratedMolecule] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const trimmedMutations = mutationsInput.trim();
  const parsedMutations = Number(trimmedMutations);
  // Only whole numbers inside the API's accepted range are sendable. Anything
  // else, including an empty field, is caught here rather than becoming a 422.
  const mutationsAreValid =
    trimmedMutations !== '' &&
    Number.isInteger(parsedMutations) &&
    parsedMutations >= 0 &&
    parsedMutations <= MAX_MUTATIONS;

  const handleGenerate = async () => {
    if (!baseMolecule) {
      toast.error('Please enter a base molecule SMILES');
      return;
    }

    if (!mutationsAreValid) {
      toast.error(
        `Number of mutations must be a whole number between 0 and ${MAX_MUTATIONS}`
      );
      return;
    }

    setIsLoading(true);
    try {
      const response = await axios.post('/generate_molecule', {
        base_smiles: baseMolecule,
        num_mutations: parsedMutations
      });

      const {
        generated_smiles,
        molecular_image,
        properties,
        original_smiles,
        requested_mutations,
        successful_mutations,
        failed_mutations,
        mutated
      } = response.data;
      setGeneratedMolecule({
        original_smiles: original_smiles,
        generated_smiles: generated_smiles,
        molecular_image: molecular_image,
        properties: properties,
        requested_mutations: requested_mutations,
        successful_mutations: successful_mutations,
        failed_mutations: failed_mutations,
        mutated: mutated
      });
      toast.success('Molecule generated successfully!');
    } catch (error) {
      console.error('Error generating molecule:', error);
      toast.error(`Failed to generate molecule: ${describeError(error)}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 py-6 flex flex-col justify-center sm:py-12">
      <div className="relative py-3 sm:max-w-xl sm:mx-auto">
        <div className="absolute inset-0 bg-gradient-to-r from-cyan-400 to-light-blue-500 shadow-lg transform -skew-y-6 sm:skew-y-0 sm:-rotate-6 sm:rounded-3xl"></div>
        <div className="relative px-4 py-10 bg-white shadow-lg sm:rounded-3xl sm:p-20">
          <div className="max-w-md mx-auto">
            <div className="divide-y divide-gray-200">
              <div className="py-8 text-base leading-6 space-y-4 text-gray-700 sm:text-lg sm:leading-7">
                <h2 className="text-3xl font-extrabold text-center text-gray-900">
                  Mole
                </h2>

                <div className="flex flex-col">
                  {/* Tied to the input by id and htmlFor. As a sibling with no
                      htmlFor the label labels nothing, and a placeholder is not
                      a reliable accessible name. */}
                  <label className="leading-loose" htmlFor="base-molecule-smiles">
                    Base Molecule SMILES
                  </label>
                  <input
                    id="base-molecule-smiles"
                    type="text"
                    className="px-4 py-2 border focus:ring-gray-500 focus:border-gray-900 w-full sm:text-sm border-gray-300 rounded-md focus:outline-none text-gray-600"
                    placeholder="Enter SMILES (e.g., CC(=O)OC1=CC=CC=C1C(=O)O)"
                    value={baseMolecule}
                    onChange={(e) => setBaseMolecule(e.target.value)}
                  />
                </div>

                <div className="flex flex-col">
                  <label className="leading-loose" htmlFor="number-of-mutations">
                    Number of Mutations
                  </label>
                  <input
                    id="number-of-mutations"
                    type="number"
                    className="px-4 py-2 border focus:ring-gray-500 focus:ring-gray-900 w-full sm:text-sm border-gray-300 rounded-md focus:outline-none text-gray-600"
                    value={mutationsInput}
                    onChange={(e) => setMutationsInput(e.target.value)}
                    min="0"
                    max={MAX_MUTATIONS}
                  />
                  {!mutationsAreValid && (
                    <p className="text-sm text-red-600 mt-1">
                      Enter a whole number between 0 and {MAX_MUTATIONS}.
                    </p>
                  )}
                </div>

                <div className="flex items-center space-x-4">
                  <button
                    onClick={handleGenerate}
                    disabled={isLoading}
                    className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
                  >
                    {isLoading ? 'Generating...' : 'Generate Molecule'}
                  </button>
                </div>
              </div>

              {generatedMolecule && (
                <div className="pt-4 flex flex-col">
                  <h3 className="text-xl font-semibold mb-2">Generated Molecule</h3>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <img
                      src={`data:image/png;base64,${generatedMolecule.molecular_image}`}
                      alt="Generated Molecule"
                      className="mx-auto mb-4 max-w-xs"
                    />
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <strong>Original SMILES:</strong>
                        <p className="text-sm">{generatedMolecule.original_smiles}</p>
                      </div>
                      <div>
                        <strong>Generated SMILES:</strong>
                        <p className="text-sm">{generatedMolecule.generated_smiles}</p>
                      </div>
                    </div>
                    <div className="mt-4">
                      <h4 className="font-semibold mb-2">
                        Mutations Applied
                      </h4>
                      <p className="text-sm">
                        {generatedMolecule.successful_mutations} of{' '}
                        {generatedMolecule.requested_mutations} applied
                        {generatedMolecule.failed_mutations > 0 && (
                          <span className="text-gray-500">
                            {' '}
                            ({generatedMolecule.failed_mutations} rejected: no
                            valid change could be made)
                          </span>
                        )}
                      </p>
                      {!generatedMolecule.mutated && (
                        <p className="text-sm text-yellow-700 mt-1">
                          No mutation could be applied. The structure shown is
                          unchanged from the input.
                        </p>
                      )}
                    </div>
                    <div className="mt-4">
                      <h4 className="font-semibold mb-2">Molecular Properties</h4>
                      <table className="w-full">
                        <tbody>
                          {Object.entries(generatedMolecule.properties).map(([key, value]) => (
                            <tr key={key} className="border-b">
                              <td className="py-1">{key}</td>
                              <td className="py-1 text-right">{value.toFixed(2)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      <ToastContainer position="bottom-right" />
    </div>
  );
}

export default App;
