import unittest
from darwin.options import options
from darwin.Model import Model
from darwin.ModelResults import ModelResults

# test_to_dict: This test checks if the to_dict() method of ModelResults class returns the expected dictionary representation of the object. It compares the dictionary returned by to_dict() with an expected dictionary to ensure that all the attributes of ModelResults object are correctly converted to a dictionary.
#
# test_from_dict: This test checks if the from_dict() method of ModelResults class correctly creates a new ModelResults object from a given dictionary. It compares the attributes of the created object with the expected attribute values to ensure that the from_dict() method works as expected.

# test_calc_fitness: This test checks if the calc_fitness() method of ModelResults class correctly calculates the fitness value based on the given Model object and the options penalties. It compares the calculated fitness value with an expected fitness value to ensure that the calc_fitness() method is calculating the fitness correctly.

class ModelResultsTestCase(unittest.TestCase):
    def setUp(self):
        options.crash_value = 999999
        self.messages = self.errors = ""

    def test_initial_values(self):
        model_results = ModelResults()
        model_results.ofv =  500

        self.assertEqual(model_results.fitness, options.crash_value)
        self.assertEqual(model_results.condition_num, options.crash_value)
        self.assertFalse(model_results.success)
        self.assertFalse(model_results.covariance)
        self.assertFalse(model_results.correlation)
        self.assertEqual(model_results.post_run_r_text, "")
        self.assertEqual(model_results.post_run_python_text, "")
        self.assertEqual(model_results.post_run_python_penalty, 0)
        self.assertEqual(model_results.post_run_r_penalty, 0)
        self.assertEqual(model_results.messages, "")
        self.assertEqual(model_results.errors, "")

    def test_to_dict(self):
        model_results = ModelResults()
        model_results.ofv =  500

        expected_dict = {
            'fitness': model_results.fitness,
            'ofv': model_results.ofv,
            'success': model_results.success,
            'covariance': model_results.covariance,
            'correlation': model_results.correlation,
            'condition_num': model_results.condition_num,
            'post_run_r_text': model_results.post_run_r_text,
            'post_run_r_penalty': model_results.post_run_r_penalty,
            'post_run_python_text': model_results.post_run_python_text,
            'post_run_python_penalty': model_results.post_run_python_penalty,
            'messages': model_results.messages,
            'errors': model_results.errors
        }
        self.assertEqual(model_results.to_dict(), expected_dict)

    def test_from_dict(self):
        src_dict = {
            'fitness': 0.5,
            'ofv': 1.2,
            'success': True,
            'covariance': False,
            'correlation': True,
            'condition_num': 10,
            'post_run_r_text': "Some R text",
            'post_run_r_penalty': 2.0,
            'post_run_python_text': "Some Python text",
            'post_run_python_penalty': 1.0,
            'messages': "Some messages",
            'errors': "Some errors"
        }
        model_results = ModelResults.from_dict(src_dict)
        self.assertEqual(model_results.fitness, 0.5)
        self.assertEqual(model_results.ofv, 1.2)
        self.assertTrue(model_results.success)
        self.assertFalse(model_results.covariance)
        self.assertTrue(model_results.correlation)
        self.assertEqual(model_results.condition_num, 10)
        self.assertEqual(model_results.post_run_r_text, "Some R text")
        self.assertEqual(model_results.post_run_r_penalty, 2.0)
        self.assertEqual(model_results.post_run_python_text, "Some Python text")
        self.assertEqual(model_results.post_run_python_penalty, 1.0)
        self.assertEqual(model_results.messages, "Some messages")
        self.assertEqual(model_results.errors, "Some errors")

    def test_calc_fitness(self):
        code = 'model code'
        model = Model(code)
        model_results = ModelResults()
        model_results.ofv =  500
        model.non_influential_token_num = 2
        model.estimated_theta_num = 3
        model.omega_num = 1
        model.sigma_num = 4
        # Set values for penalties
        penalties = {
            'non_influential_tokens': 1,
            'convergence': 2,
            'covariance': 3,
            'correlation': 4,
            'condition_number': 5,
            'theta': 6,
            'omega': 7,
            'sigma': 8
        }
        options.penalty = penalties

        # Call the calc_fitness() method
        fitness = model_results.calc_fitness(model)

        # Expected fitness value
        expected_fitness = (model_results.ofv +
                            model.non_influential_token_num * penalties['non_influential_tokens'] +
                            penalties['convergence'] +
                            penalties['covariance'] +
                            penalties['correlation'] +
                            penalties['condition_number'] +
                            model.estimated_theta_num * penalties['theta'] +
                            model.omega_num * penalties['omega'] +
                            model.sigma_num * penalties['sigma'] +
                            model_results.post_run_r_penalty +
                            model_results.post_run_python_penalty)

        # Check if the calculated fitness value matches the expected fitness value
        self.assertEqual(fitness, expected_fitness)


