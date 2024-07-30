import { Box, Stack } from '@mui/material'
import { ErrorBoundary } from 'react-error-boundary'
import { Graph } from '../Graph/Graph'
import { TextContainer } from '../Layouts'
import { Link } from '../components/Link'
import { SectionErrorDisplay } from '../components/SectionErrorDisplay'
import toolAdjust from '../images/intro/corner.png'

export const GraphPage = (props) => {
  return (
    <>
      <div className="non-print">
        <h1>Resource Splitting Tool</h1>

        <Box
          component="img"
          src={toolAdjust}
          alt="The fair division tool. A graph shows two rectangular segments and the mouse moving the corner of an angled segment."
          maxWidth={550}
          width={'100%'}
          sx={{ float: { xs: 'none', lg: 'right' } }}
          marginLeft={{ xs: 0, lg: 4 }}
          marginY={2}
        />
        <TextContainer>
          <p>
            Welcome to our visual <strong>Resource Splitting Tool</strong>, the first of
            its kind! Using this tool you can split a resource fairly based on the
            preferences of each person, which our intelligent <strong>algorithm</strong>{' '}
            will then split evenly among all users.
          </p>
        </TextContainer>

        <TextContainer>
          <p>
            The tool works with <strong>divisible resources</strong> like time, cake, or
            land. Currently, our algorithms support 2-4 participants. In the future we
            plan to introduce new algorithms for indivisible items and for more
            participants.
          </p>
          <p>
            This is primarily an <strong>educational tool</strong>, but concepts about
            fairness help in real life too.
          </p>
          <p>
            Explore our{' '}
            <strong>
              <Link href="/learn">Interactive Course</Link>
            </strong>{' '}
            to learn how fair division works.
          </p>
        </TextContainer>
      </div>
      <Box marginTop={10} marginBottom={10} id="graph-content">
        <ErrorBoundary FallbackComponent={SectionErrorDisplay}>
          <Graph {...props} />
        </ErrorBoundary>
      </Box>

      <div className="non-print">
        <h3>Feeling Lost?</h3>
        <p>
          See the <Link href="/learn">Interactive Course</Link> for an introduction to
          fair division or the <Link href="/help">Help Page</Link> for clarification on
          how this tool works.
        </p>
      </div>
    </>
  )
}
