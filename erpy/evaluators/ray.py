from dataclasses import dataclass
from typing import Callable

from ray.util import ActorPool
from tqdm import tqdm

from erpy.base.evaluator import Evaluator, EvaluatorConfig
from erpy.base.population import Population


@dataclass
class DistributedEvaluatorConfig(EvaluatorConfig):
    num_workers: int
    actor_generator: Callable[[EvaluatorConfig], Evaluator]
    num_cores_per_worker: int


class RayDistributedEvaluator(Evaluator):
    def __init__(self, config: DistributedEvaluatorConfig):
        super(RayDistributedEvaluator, self).__init__(config=config)

        self.pool: ActorPool = self._build_pool()

    @property
    def config(self) -> DistributedEvaluatorConfig:
        return self.config

    def _build_pool(self) -> ActorPool:
        workers = [self.config.actor_generator(self.config) for _ in range(self.config.num_workers)]
        return ActorPool(workers)

    def evaluate(self, population: Population) -> None:
        all_genomes = population.genomes
        target_genome_ids = population.to_evaluate

        target_genomes = [all_genomes[genome_id] for genome_id in target_genome_ids]

        for genome in tqdm(target_genomes, desc=f"Gen {population.generation}\t-\tSending jobs to workers."):
            self.pool.submit(
                lambda worker, genome: worker.run.remote(genome), genome)
            population.under_evaluation.append(genome.genome_id)

        population.to_evaluate.clear()
        population.evaluation_results.clear()

        timeout = None
        while self.pool.has_next():
            try:
                evaluation_result = self.pool.get_next_unordered(timeout=timeout)
                genome = all_genomes[evaluation_result.genome_id]
                population.evaluation_results.append(evaluation_result)
                population.under_evaluation.remove(genome.genome_id)
                timeout = 5
            except TimeoutError:
                break
